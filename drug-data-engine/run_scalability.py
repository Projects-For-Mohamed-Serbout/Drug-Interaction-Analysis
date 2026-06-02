"""
Scalability Benchmark — MongoDB vs Neo4j (anteproyecto Phase 4/5: "scalability").

Measures how query latency grows as the volume of processed data increases.
Instead of duplicating the databases (not feasible on a single cloud Neo4j
instance), each representative query is scoped to a growing subset of the data
by an indexed key (`cod_nacion`): the first 25%, 50%, 75% and 100% of drugs and
their interactions. This yields a latency-vs-data-volume curve for each query on
each database, using the SAME query logic as run_benchmarks.py.

Queries chosen are the ones whose cost scales with data volume (aggregations,
filtered scans, group-by). They return counts (not large row sets) so the
measurement reflects engine work, not network transfer of results.

Usage:
    python run_scalability.py
    python run_scalability.py --iterations 20
"""
import argparse
import csv
import json
import logging
import statistics
import time
from datetime import datetime
from pathlib import Path

from pymongo import MongoClient
from neo4j import GraphDatabase

from src.config import get_settings
from src.utils import setup_logging

logger = logging.getLogger(__name__)

FRACTIONS = [0.25, 0.50, 0.75, 1.00]
WARMUP = 3


# =========================================================================
# Timing helper (mirrors run_benchmarks.py methodology: warmup + measured)
# =========================================================================
def measure(fn, iterations):
    """Run fn warmup+iterations times; return (median_ms, p95_ms, rows)."""
    for _ in range(WARMUP):
        fn()
    times = []
    rows = 0
    for _ in range(iterations):
        t0 = time.perf_counter()
        rows = fn()
        times.append((time.perf_counter() - t0) * 1000)
    times.sort()
    median = statistics.median(times)
    k = int(0.95 * (len(times) - 1))
    return round(median, 2), round(times[k], 2), rows


# =========================================================================
# MongoDB scoped queries (scope = medicamento_origen.cod_nacion <= threshold)
# =========================================================================
class MongoScaled:
    def __init__(self, db):
        self.db = db
        self.col = db['drug_interactions']

    def _scope(self, threshold):
        return {} if threshold is None else {'medicamento_origen.cod_nacion': {'$lte': threshold}}

    def count_by_severity(self, t):  # aggregation
        p = [{'$match': {**self._scope(t), 'interaccion.nlp.severidad': {'$ne': None}}},
             {'$group': {'_id': '$interaccion.nlp.severidad', 'c': {'$sum': 1}}}]
        return len(list(self.col.aggregate(p)))

    def count_contraindicated(self, t):  # filtered scan -> count
        q = {**self._scope(t), 'interaccion.nlp.severidad': 'contraindicated'}
        return self.col.count_documents(q)

    def count_cardiac(self, t):  # filtered scan -> count
        q = {**self._scope(t), 'interaccion.nlp.tipo': 'cardiac'}
        return self.col.count_documents(q)

    def top_interacting(self, t):  # group + sort + limit
        p = [{'$match': self._scope(t)},
             {'$group': {'_id': '$medicamento_origen.cod_nacion', 'c': {'$sum': 1}}},
             {'$sort': {'c': -1}}, {'$limit': 10}]
        return len(list(self.col.aggregate(p)))


# =========================================================================
# Neo4j scoped queries (scope = d.cod_nacion <= threshold)
# =========================================================================
class Neo4jScaled:
    def __init__(self, driver):
        self.driver = driver

    def _run(self, query, params):
        with self.driver.session() as s:
            return s.run(query, params).single()[0]

    def count_by_severity(self, t):
        where = "WHERE i.severidad IS NOT NULL" + ("" if t is None else " AND d.cod_nacion <= $t")
        q = (f"MATCH (d:Drug)-[i:INTERACTS_WITH_ATC]->() {where} "
             "WITH i.severidad AS sev, count(*) AS c RETURN count(sev) AS n")
        return self._run(q, {'t': t})

    def count_contraindicated(self, t):
        where = "WHERE i.severidad = 'contraindicated'" + ("" if t is None else " AND d.cod_nacion <= $t")
        q = f"MATCH (d:Drug)-[i:INTERACTS_WITH_ATC]->() {where} RETURN count(i) AS n"
        return self._run(q, {'t': t})

    def count_cardiac(self, t):
        where = "WHERE i.tipo = 'cardiac'" + ("" if t is None else " AND d.cod_nacion <= $t")
        q = f"MATCH (d:Drug)-[i:INTERACTS_WITH_ATC]->() {where} RETURN count(i) AS n"
        return self._run(q, {'t': t})

    def top_interacting(self, t):
        where = "" if t is None else "WHERE d.cod_nacion <= $t"
        q = (f"MATCH (d:Drug)-[i:INTERACTS_WITH_ATC]->() {where} "
             "WITH d, count(i) AS c RETURN c ORDER BY c DESC LIMIT 10")
        with self.driver.session() as s:
            return len(list(s.run(q, {'t': t})))


QUERIES = [
    ('count_by_severity', 'Aggregation: count interactions grouped by severity'),
    ('count_contraindicated', 'Filtered scan: count contraindicated interactions'),
    ('count_cardiac', 'Filtered scan: count cardiac interactions'),
    ('top_interacting', 'Group+sort: top 10 drugs by interaction count'),
]


def compute_thresholds(db):
    """cod_nacion value at each percentile (drugs sorted by cod_nacion)."""
    codes = sorted(c for c in db['drugs'].distinct('cod_nacion') if c)
    n = len(codes)
    thresholds = {}
    for f in FRACTIONS:
        # Always keep the same predicate SHAPE across sizes (only the volume
        # changes) so the curve isolates data volume, not query shape. At 100%
        # the threshold is the maximum cod_nacion, which matches all drugs.
        thresholds[f] = codes[min(int(f * n), n) - 1]
    return thresholds, n


def parse_args():
    p = argparse.ArgumentParser(description="Scalability benchmark: MongoDB vs Neo4j")
    p.add_argument('--iterations', type=int, default=20)
    p.add_argument('--output', default='scalability_results')
    p.add_argument('--log-level', default='INFO')
    return p.parse_args()


def main():
    global logger
    args = parse_args()
    logger = setup_logging(args.log_level)
    settings = get_settings()

    logger.info("=" * 64)
    logger.info("SCALABILITY BENCHMARK — MongoDB vs Neo4j")
    logger.info(f"Data sizes: {[int(f*100) for f in FRACTIONS]}%  | iterations: {args.iterations}")
    logger.info("=" * 64)

    m = MongoClient(settings.mongodb_uri)
    db = m[settings.mongodb_db]
    d = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))

    try:
        m.admin.command('ping'); d.verify_connectivity()
        thresholds, n_drugs = compute_thresholds(db)
        logger.info(f"Total drugs: {n_drugs}. cod_nacion thresholds: "
                    + ", ".join(f"{int(f*100)}%={thresholds[f] or 'ALL'}" for f in FRACTIONS))

        mongo = MongoScaled(db)
        neo = Neo4jScaled(d)

        results = []  # rows: query, db, size_pct, median_ms, p95_ms, rows
        for qname, qdesc in QUERIES:
            for f in FRACTIONS:
                t = thresholds[f]
                for label, obj in (('MongoDB', mongo), ('Neo4j', neo)):
                    fn = lambda obj=obj, qname=qname, t=t: getattr(obj, qname)(t)
                    med, p95, rows = measure(fn, args.iterations)
                    results.append({'query': qname, 'database': label,
                                    'size_pct': int(f * 100), 'median_ms': med,
                                    'p95_ms': p95, 'result': rows})
                    logger.info(f"  {qname:<22} {label:<8} {int(f*100):>3}%  "
                                f"median={med:>8.2f} ms  p95={p95:>8.2f}  (result={rows})")

        # --- Scaling summary: latency growth 25% -> 100% per query/db ---
        logger.info("")
        logger.info("SCALING FACTOR (median latency at 100% / at 25%):")
        logger.info(f"  {'Query':<22} {'MongoDB':>10} {'Neo4j':>10}")
        for qname, _ in QUERIES:
            def factor(dbname):
                lo = next(r['median_ms'] for r in results
                          if r['query'] == qname and r['database'] == dbname and r['size_pct'] == 25)
                hi = next(r['median_ms'] for r in results
                          if r['query'] == qname and r['database'] == dbname and r['size_pct'] == 100)
                return hi / lo if lo > 0 else 0
            logger.info(f"  {qname:<22} {factor('MongoDB'):>9.2f}x {factor('Neo4j'):>9.2f}x")

        # --- Save ---
        results_dir = Path(__file__).parent / 'results'
        results_dir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report = {
            'generated_at': datetime.now().isoformat(),
            'method': 'cod_nacion-scoped subsets (25/50/75/100%); counts to isolate engine work',
            'iterations': args.iterations, 'warmup': WARMUP,
            'total_drugs': n_drugs,
            'thresholds': {str(int(f*100)): thresholds[f] for f in FRACTIONS},
            'results': results,
        }
        (results_dir / f"{args.output}_{stamp}.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        with open(results_dir / f"{args.output}_{stamp}.csv", 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=results[0].keys()); w.writeheader(); w.writerows(results)
        logger.info(f"\nSaved results/{args.output}_{stamp}.json + .csv")
    finally:
        m.close(); d.close()


if __name__ == '__main__':
    main()
