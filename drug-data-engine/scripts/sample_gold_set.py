"""
Gold-Set Sampler — build an INDEPENDENT evaluation set for the NLP pipeline.

The original evaluation used 44 hand-written examples annotated with the same
criteria the rules encode (circular). This script draws a fresh sample of REAL
interactions from MongoDB for manual annotation, decoupling the gold standard
from the classifier.

Key design choices (for methodological defensibility):
  * Sampled from the live CIMA corpus, not curated by hand.
  * De-duplicated by (efecto + recomendacion) so repeated boilerplate text does
    not inflate any one class.
  * Reproducible: fixed random seed, sorted candidate pool.
  * Label columns are left BLANK — the annotator is NOT shown any model
    prediction, so there is no anchoring bias. (In --balanced mode the regex
    prediction is used ONLY to spread the sample across severity classes; it is
    never written as a label.)

Usage:
    python -m scripts.sample_gold_set --n 200 --output data/gold_set.csv
    python -m scripts.sample_gold_set --n 200 --balanced --output data/gold_set.csv

Then annotate the CSV (fill true_severity / true_type / true_mechanism) and run:
    python -m scripts.evaluate_nlp --gold-csv data/gold_set.csv --output results/
"""
import argparse
import csv
import logging
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import List, Dict

from src.utils import setup_logging
from src.config.settings import get_settings
from src.services.mongodb_service import MongoDBService

logger = logging.getLogger(__name__)

# Controlled vocabularies the annotator must use (kept in sync with the pipeline).
SEVERITY_LABELS = ["contraindicated", "severe", "moderate", "mild", "unknown"]
TYPE_LABELS = [
    "cardiac", "cns", "hemorrhagic", "gastrointestinal", "renal", "hepatic",
    "metabolic", "muscular", "toxicity", "efficacy_reduction", "efficacy_increase",
    "respiratory", "other",
]
MECHANISM_LABELS = ["pharmacokinetic", "pharmacodynamic", "unknown"]

SEED = 42


def _norm(text: str) -> str:
    """Normalise text for de-duplication."""
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def load_candidates(db) -> List[Dict]:
    """Pull distinct (efecto, recomendacion) interactions from MongoDB."""
    cursor = db["drug_interactions"].find(
        {"interaccion.efecto": {"$exists": True, "$ne": ""}},
        {
            "medicamento_origen.cod_nacion": 1,
            "medicamento_origen.nombre": 1,
            "medicamento_destino.nombre": 1,
            "interaccion.efecto": 1,
            "interaccion.recomendacion": 1,
        },
    )

    seen = set()
    candidates = []
    for doc in cursor:
        inter = doc.get("interaccion", {})
        efecto = inter.get("efecto", "")
        recom = inter.get("recomendacion", "")
        key = (_norm(efecto), _norm(recom))
        if not key[0] or key in seen:
            continue
        seen.add(key)
        candidates.append({
            "cod_origen": doc.get("medicamento_origen", {}).get("cod_nacion", ""),
            "nombre_origen": doc.get("medicamento_origen", {}).get("nombre", ""),
            "nombre_destino": doc.get("medicamento_destino", {}).get("nombre", ""),
            "efecto": efecto,
            "recomendacion": recom,
        })

    # deterministic order before sampling → reproducible with a fixed seed
    candidates.sort(key=lambda c: (_norm(c["efecto"]), _norm(c["recomendacion"])))
    return candidates


def sample_random(candidates: List[Dict], n: int, rng: random.Random) -> List[Dict]:
    """Plain random sample reflecting the corpus distribution."""
    if n >= len(candidates):
        logger.warning("Requested %d but only %d distinct candidates available.", n, len(candidates))
        return list(candidates)
    return rng.sample(candidates, n)


def sample_balanced(candidates: List[Dict], n: int, rng: random.Random) -> List[Dict]:
    """
    Spread the sample across severity classes using the regex prediction as a
    SAMPLING AID ONLY (never written as a label). Guarantees rare-class coverage.
    """
    from src.nlp import NLPPipeline
    pipeline = NLPPipeline()

    buckets: Dict[str, List[Dict]] = defaultdict(list)
    for c in candidates:
        pred = pipeline.analyze(c["efecto"], c["recomendacion"]).severity
        buckets[str(pred)].append(c)

    per_class = max(1, n // len(SEVERITY_LABELS))
    chosen: List[Dict] = []
    for label in SEVERITY_LABELS:
        pool = buckets.get(label, [])
        rng.shuffle(pool)
        chosen.extend(pool[:per_class])

    # top up to n from whatever remains, at random
    if len(chosen) < n:
        chosen_keys = {(_norm(c["efecto"]), _norm(c["recomendacion"])) for c in chosen}
        remaining = [c for c in candidates
                     if (_norm(c["efecto"]), _norm(c["recomendacion"])) not in chosen_keys]
        rng.shuffle(remaining)
        chosen.extend(remaining[: n - len(chosen)])

    rng.shuffle(chosen)
    return chosen[:n]


def write_csv(rows: List[Dict], output: Path):
    """Write the annotation CSV (blank label columns) + a label guide."""
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "idx", "cod_origen", "nombre_origen", "nombre_destino",
        "efecto", "recomendacion",
        "true_severity", "true_type", "true_mechanism",
    ]
    # utf-8-sig so the accented Spanish text opens cleanly in Excel
    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, r in enumerate(rows, 1):
            writer.writerow({
                "idx": i,
                "cod_origen": r["cod_origen"],
                "nombre_origen": r["nombre_origen"],
                "nombre_destino": r["nombre_destino"],
                "efecto": r["efecto"],
                "recomendacion": r["recomendacion"],
                "true_severity": "",
                "true_type": "",
                "true_mechanism": "",
            })

    guide = output.with_name(output.stem + "_LABELS.txt")
    with open(guide, "w", encoding="utf-8") as f:
        f.write("ANNOTATION GUIDE — allowed labels (fill exactly one per column)\n")
        f.write("=" * 60 + "\n\n")
        f.write("true_severity : " + " | ".join(SEVERITY_LABELS) + "\n")
        f.write("true_type     : " + " | ".join(TYPE_LABELS) + "\n")
        f.write("true_mechanism: " + " | ".join(MECHANISM_LABELS) + "\n\n")
        f.write("Guidance:\n")
        f.write("  severity  — judge from the CLINICAL text, not the rule keywords.\n")
        f.write("              contraindicated > severe > moderate > mild > unknown.\n")
        f.write("  type      — primary organ system / pharmacological effect.\n")
        f.write("  mechanism — pharmacokinetic (absorption/metabolism/CYP/levels),\n")
        f.write("              pharmacodynamic (additive/synergistic effect),\n")
        f.write("              unknown (mechanism not stated in the text).\n")
    logger.info("Label guide written to: %s", guide)


def parse_args():
    p = argparse.ArgumentParser(description="Sample an independent NLP gold set from MongoDB")
    p.add_argument("--n", type=int, default=200, help="number of interactions to sample")
    p.add_argument("--balanced", action="store_true",
                   help="spread across severity classes (regex used only as sampling aid)")
    p.add_argument("--output", type=str, default="data/gold_set.csv")
    p.add_argument("--log-level", default="INFO")
    return p.parse_args()


def main():
    args = parse_args()
    setup_logging(args.log_level)
    settings = get_settings()

    if not settings.mongodb_uri:
        logger.error("mongodb_uri not configured in .env")
        return

    service = MongoDBService(settings.mongodb_uri, settings.mongodb_db)
    if not service.connect():
        logger.error("Could not connect to MongoDB.")
        return

    try:
        logger.info("Loading distinct interaction texts from MongoDB...")
        candidates = load_candidates(service.db)
        logger.info("Found %d distinct (efecto, recomendacion) interactions.", len(candidates))

        rng = random.Random(SEED)
        if args.n >= len(candidates):
            # The corpus has very few distinct texts — annotate them ALL. This
            # is a CENSUS of every unique interaction description (zero selection
            # bias), which is stronger than any sample.
            logger.info("Requested %d >= %d distinct texts: taking the FULL CENSUS "
                        "of all distinct interaction descriptions.", args.n, len(candidates))
            rows = list(candidates)
        elif args.balanced:
            logger.info("Sampling %d with severity balancing (regex as sampling aid only)...", args.n)
            rows = sample_balanced(candidates, args.n, rng)
        else:
            logger.info("Random sampling %d (reflects corpus distribution)...", args.n)
            rows = sample_random(candidates, args.n, rng)

        output = Path(args.output)
        write_csv(rows, output)
        logger.info("Wrote %d rows to annotate -> %s", len(rows), output)
        logger.info("Next: fill true_severity / true_type / true_mechanism, then run "
                    "`python -m scripts.evaluate_nlp --gold-csv %s --output results/`", output)
    finally:
        service.disconnect()


if __name__ == "__main__":
    main()
