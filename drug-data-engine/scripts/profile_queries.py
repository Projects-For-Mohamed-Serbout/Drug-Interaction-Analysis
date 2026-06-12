"""
Server-side query profiling — isolate database work from network latency.

The wall-clock benchmark (scripts/.. -> src/benchmarks) times each query from a
local client to MongoDB Atlas / Neo4j Aura, so its numbers include the network
round-trip (a ~35-50 ms floor even on trivial lookups). This script captures the
SERVER-SIDE execution time and the query PLAN for the comparable queries, using:

  * MongoDB : db.command('explain', ..., verbosity='executionStats')
              -> executionTimeMillis, docs/keys examined, winning plan + index
  * Neo4j   : PROFILE <cypher>
              -> result_available_after + result_consumed_after (server ms),
                 total db hits, operators (proves index vs scan)

For each query it also records a short wall-clock median, so the report shows
network overhead = wall_clock - server_side. This addresses RQ2 (fair, network-
independent timing) and RQ3 (query plans = optimization / index-usage evidence).

Usage:
    python -m scripts.profile_queries --output results/
"""
import argparse
import json
import logging
import statistics
import time
from datetime import datetime
from pathlib import Path

from pymongo import MongoClient
from neo4j import GraphDatabase

from src.config.settings import get_settings
from src.utils import setup_logging

logger = logging.getLogger(__name__)

# Sample parameters — identical to src/benchmarks/*_benchmark.py
DRUG_ID = '600023'
ATC_PREFIX = 'N06'

# Comparable queries, mirroring the benchmark definitions.
QUERIES = [
    {
        'id': 'Q1', 'category': 'Point Lookup', 'name': 'Drug by national code',
        'mongo': {'op': 'find', 'coll': 'drugs', 'filter': {'cod_nacion': DRUG_ID}, 'limit': 1},
        'cypher': 'MATCH (d:Drug {cod_nacion:$id}) RETURN d', 'params': {'id': DRUG_ID},
    },
    {
        'id': 'Q2', 'category': 'Relationship Traversal', 'name': 'Interactions for a drug',
        'mongo': {'op': 'find', 'coll': 'drug_interactions',
                  'filter': {'medicamento_origen.cod_nacion': DRUG_ID},
                  'proj': {'medicamento_destino.atc': 1, 'interaccion.efecto': 1}},
        'cypher': ('MATCH (d:Drug {cod_nacion:$id})-[i:INTERACTS_WITH_ATC]->(a:ATCCode) '
                   'RETURN a.codigo AS target_atc, i.efecto AS effect'),
        'params': {'id': DRUG_ID},
    },
    {
        'id': 'Q3', 'category': 'Range Scan', 'name': 'Contraindicated interactions',
        'mongo': {'op': 'find', 'coll': 'drug_interactions',
                  'filter': {'interaccion.nlp.severidad': 'contraindicated'},
                  'proj': {'interaccion.efecto': 1}, 'limit': 1000},
        'cypher': ("MATCH (d:Drug)-[i:INTERACTS_WITH_ATC]->(a:ATCCode) "
                   "WHERE i.severidad = 'contraindicated' "
                   "RETURN a.codigo AS target_atc, i.efecto AS effect LIMIT 1000"),
        'params': {},
    },
    {
        'id': 'Q6', 'category': 'Aggregation', 'name': 'Count interactions by severity',
        'mongo': {'op': 'agg', 'coll': 'drug_interactions', 'pipeline': [
            {'$match': {'interaccion.nlp.severidad': {'$exists': True, '$ne': None}}},
            {'$group': {'_id': '$interaccion.nlp.severidad', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
        ]},
        'cypher': ('MATCH ()-[i:INTERACTS_WITH_ATC]->() WHERE i.severidad IS NOT NULL '
                   'RETURN i.severidad AS _id, count(*) AS count ORDER BY count DESC'),
        'params': {},
    },
    {
        'id': 'Q7', 'category': 'Range Scan', 'name': 'Drugs by ATC prefix',
        'mongo': {'op': 'find', 'coll': 'drugs',
                  'filter': {'atc.codigo': {'$regex': f'^{ATC_PREFIX}'}},
                  'proj': {'cod_nacion': 1, 'atc.codigo': 1}, 'limit': 500},
        'cypher': ('MATCH (d:Drug)-[:CLASSIFIED_AS]->(a:ATCCode) '
                   'WHERE a.codigo STARTS WITH $prefix '
                   'RETURN DISTINCT d.cod_nacion AS cod_nacion, a.codigo AS atc LIMIT 500'),
        'params': {'prefix': ATC_PREFIX},
    },
    {
        'id': 'Q8', 'category': 'Complex Filter', 'name': 'Severe cardiac interactions in ATC class',
        'mongo': {'op': 'find', 'coll': 'drug_interactions', 'filter': {
            'interaccion.nlp.severidad': {'$in': ['contraindicated', 'severe']},
            'interaccion.nlp.tipo': 'cardiac',
            'medicamento_origen.atc': {'$regex': f'^{ATC_PREFIX}'},
        }, 'limit': 500},
        'cypher': ("MATCH (d:Drug)-[i:INTERACTS_WITH_ATC]->(a:ATCCode) "
                   "MATCH (d)-[:CLASSIFIED_AS]->(drug_atc:ATCCode) "
                   "WHERE drug_atc.codigo STARTS WITH $atc_prefix "
                   "AND i.severidad IN ['contraindicated','severe'] AND i.tipo = 'cardiac' "
                   "RETURN d.nombre_comercial AS source_drug, a.codigo AS target_atc LIMIT 500"),
        'params': {'atc_prefix': ATC_PREFIX},
    },
    {
        'id': 'Q9', 'category': 'Aggregation', 'name': 'Top interacting drugs',
        'mongo': {'op': 'agg', 'coll': 'drug_interactions', 'pipeline': [
            {'$group': {'_id': '$medicamento_origen.cod_nacion',
                        'nombre': {'$first': '$medicamento_origen.nombre'},
                        'interaction_count': {'$sum': 1}}},
            {'$sort': {'interaction_count': -1}},
            {'$limit': 10},
        ]},
        'cypher': ('MATCH (d:Drug)-[i:INTERACTS_WITH_ATC]->() '
                   'RETURN d.cod_nacion AS cod_nacion, count(i) AS interaction_count '
                   'ORDER BY interaction_count DESC LIMIT 10'),
        'params': {},
    },
]

WALL_RUNS = 10
WALL_WARMUP = 2
SERVER_RUNS = 5  # repeat explain/PROFILE to report median + spread


def _agg(times):
    """Median/min/max of a list of ms timings."""
    vals = [t for t in times if t is not None]
    if not vals:
        return {'median': None, 'min': None, 'max': None, 'runs': 0}
    return {
        'median': round(statistics.median(vals), 2),
        'min': round(min(vals), 2),
        'max': round(max(vals), 2),
        'runs': len(vals),
    }


# ----------------------------- helpers -----------------------------

def _collect(obj, key):
    """Recursively collect all values for `key` in a nested dict/list."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                out.append(v)
            out.extend(_collect(v, key))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_collect(v, key))
    return out


def mongo_server_side(db, spec, runs=SERVER_RUNS):
    """Run explain(executionStats) `runs` times; report median time + plan."""
    coll = spec['coll']
    if spec['op'] == 'find':
        cmd = {'find': coll, 'filter': spec['filter']}
        if spec.get('proj'):
            cmd['projection'] = spec['proj']
        if spec.get('limit'):
            cmd['limit'] = spec['limit']
    else:  # aggregate
        cmd = {'aggregate': coll, 'pipeline': spec['pipeline'], 'cursor': {}}

    times = []
    exp = None
    for _ in range(runs):
        exp = db.command('explain', cmd, verbosity='executionStats')
        ets = _collect(exp, 'executionTimeMillis')
        times.append(max(ets) if ets else None)

    docs = max(_collect(exp, 'totalDocsExamined') or [0]) if _collect(exp, 'totalDocsExamined') else None
    keys = max(_collect(exp, 'totalKeysExamined') or [0]) if _collect(exp, 'totalKeysExamined') else None
    n_ret = max(_collect(exp, 'nReturned') or [0]) if _collect(exp, 'nReturned') else None
    stages = set(_collect(exp, 'stage'))
    indexes = sorted(set(_collect(exp, 'indexName')))
    used_index = any(s in stages for s in ('IXSCAN', 'COUNT_SCAN', 'DISTINCT_SCAN', 'EXPRESS_IXSCAN')) or bool(indexes)
    agg = _agg(times)
    return {
        'server_ms': agg['median'],
        'server_ms_spread': agg,
        'docs_examined': docs,
        'keys_examined': keys,
        'returned': n_ret,
        'indexes': indexes,
        'used_index': used_index,
        'scan': 'COLLSCAN' if 'COLLSCAN' in stages else ('IXSCAN' if 'IXSCAN' in stages else sorted(stages)[:1]),
    }


def _sum_db_hits(plan):
    """Recursively sum dbHits over a Neo4j profile plan dict."""
    if not isinstance(plan, dict):
        return 0
    total = plan.get('dbHits', 0) or 0
    for child in plan.get('children', []) or []:
        total += _sum_db_hits(child)
    return total


def _operators(plan, acc=None):
    if acc is None:
        acc = []
    if isinstance(plan, dict):
        op = plan.get('operatorType')
        if op:
            acc.append(op)
        for child in plan.get('children', []) or []:
            _operators(child, acc)
    return acc


def neo4j_server_side(driver, cypher, params, runs=SERVER_RUNS):
    """Run PROFILE `runs` times; report median server time + db hits + plan."""
    times = []
    profile, rows = {}, None
    with driver.session() as session:
        for _ in range(runs):
            res = session.run('PROFILE ' + cypher, params or {})
            rows = len(list(res))
            summ = res.consume()
            avail = summ.result_available_after or 0
            consumed = summ.result_consumed_after or 0
            times.append(avail + consumed)
            profile = summ.profile or {}
    ops = _operators(profile)
    agg = _agg(times)
    return {
        'server_ms': agg['median'],
        'server_ms_spread': agg,
        'db_hits': _sum_db_hits(profile),
        'rows': rows,
        'operators': ops,
        'used_index': any('Index' in o for o in ops),
    }


def wall_clock(fn):
    """Median wall-clock ms over WALL_RUNS (incl. network)."""
    for _ in range(WALL_WARMUP):
        fn()
    times = []
    for _ in range(WALL_RUNS):
        t = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t) * 1000)
    return round(statistics.median(times), 2)


# ----------------------------- main -----------------------------

def parse_args():
    p = argparse.ArgumentParser(description='Profile server-side query performance')
    p.add_argument('--output', type=str, default=None, help='Directory to save JSON report')
    p.add_argument('--log-level', default='INFO')
    return p.parse_args()


def main():
    args = parse_args()
    setup_logging(args.log_level)
    s = get_settings()

    mongo = MongoClient(s.mongodb_uri)
    db = mongo[s.mongodb_db]
    driver = GraphDatabase.driver(s.neo4j_uri, auth=(s.neo4j_user, s.neo4j_password))
    driver.verify_connectivity()

    results = []
    logger.info("Profiling %d comparable queries (server-side + wall-clock)...", len(QUERIES))
    for q in QUERIES:
        row = {'id': q['id'], 'category': q['category'], 'name': q['name']}
        # --- MongoDB ---
        try:
            spec = q['mongo']
            if spec['op'] == 'find':
                proj = spec.get('proj')
                lim = spec.get('limit', 0)
                row['mongo'] = mongo_server_side(db, spec)
                row['mongo']['wall_ms'] = wall_clock(
                    lambda: list(db[spec['coll']].find(spec['filter'], proj).limit(lim or 0))
                )
            else:
                row['mongo'] = mongo_server_side(db, spec)
                row['mongo']['wall_ms'] = wall_clock(
                    lambda: list(db[spec['coll']].aggregate(spec['pipeline']))
                )
        except Exception as e:
            row['mongo'] = {'error': str(e)}
            logger.warning("  %s MongoDB failed: %s", q['id'], e)
        # --- Neo4j ---
        try:
            row['neo4j'] = neo4j_server_side(driver, q['cypher'], q['params'])
            row['neo4j']['wall_ms'] = wall_clock(
                lambda: list(driver.session().run(q['cypher'], q['params']))
            )
        except Exception as e:
            row['neo4j'] = {'error': str(e)}
            logger.warning("  %s Neo4j failed: %s", q['id'], e)
        results.append(row)
        logger.info("  %s %-32s done", q['id'], q['name'])

    mongo.close()
    driver.close()

    # --- print contrast table ---
    def fmt(side):
        if 'error' in side:
            return 'ERR'
        sp = side.get('server_ms_spread', {})
        rng = f"({sp.get('min')}-{sp.get('max')})" if sp.get('runs', 0) > 1 else ""
        return f"{side.get('server_ms','?')}{rng} / {side.get('wall_ms','?')}ms"

    logger.info("\nserver median (min-max over %d runs) / wall median", SERVER_RUNS)
    logger.info("%-4s %-22s | %-30s | %-30s", "Q", "category", "MongoDB server/wall", "Neo4j server/wall")
    logger.info("-" * 96)
    for r in results:
        logger.info("%-4s %-22s | %-30s | %-30s", r['id'], r['category'],
                    fmt(r.get('mongo', {})), fmt(r.get('neo4j', {})))

    if args.output:
        outdir = Path(args.output)
        outdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        report = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'note': 'server_ms = median DB-reported execution time over '
                        f'{SERVER_RUNS} runs (network-independent); '
                        'wall_ms = client round-trip median incl. network',
                'server_runs': SERVER_RUNS,
                'mongodb_db': s.mongodb_db,
            },
            'queries': results,
        }
        out = outdir / f'query_profiles_{ts}.json'
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info("\nSaved: %s", out)


if __name__ == '__main__':
    main()
