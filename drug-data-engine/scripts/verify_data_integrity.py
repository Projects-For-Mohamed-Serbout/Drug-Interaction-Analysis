"""
ETL Data Integrity Verification.

Implements the anteproyecto Phase 3 requirement: "...verifying data integrity."

It reconciles the THREE views of the dataset:
    1. Source of truth   -> CIMA XML files
    2. Document store     -> MongoDB collections
    3. Graph store        -> Neo4j nodes & relationships

and runs referential-integrity checks on each store. The interaction count
difference between MongoDB (raw rows) and Neo4j (unique drug->ATC edges) is
explained explicitly (duplicate-source-row collapse), not hidden.

A machine-readable report is written to results/integrity_report_<timestamp>.json
so the numbers can be cited directly in the memoria.

Usage:
    python -m scripts.verify_data_integrity
    python -m scripts.verify_data_integrity --skip-xml      # DB-only (fast)
"""
import argparse
import json
import logging
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path

from pymongo import MongoClient
from neo4j import GraphDatabase

from src.config import get_settings
from src.utils import setup_logging
from src.extractors import DictionaryExtractor

logger = logging.getLogger(__name__)

NS = "{http://schemas.aemps.es/prescripcion/aemps_prescripcion}"

# How each MongoDB reference collection / Neo4j node label maps to the
# DictionaryExtractor key, so we can compare all three.
REFERENCE_MAP = [
    # (report label, extractor key, mongo collection, neo4j label or None)
    ("active_ingredients", "active_ingredients", "active_ingredients", "ActiveIngredient"),
    ("laboratories", "laboratories", "laboratories", "Laboratory"),
    ("atc_codes", "atc_codes", "atc_codes", "ATCCode"),
    ("pharmaceutical_forms", "pharmaceutical_forms", "pharmaceutical_forms", "PharmaceuticalForm"),
    ("administration_routes", "administration_routes", "administration_routes", "AdministrationRoute"),
    ("excipients", "excipients", "excipients", "Excipient"),
    ("package_types", "package_types", "package_types", "PackageType"),
    ("content_units", "content_units", "content_units", None),
    ("registration_statuses", "registration_statuses", "registration_statuses", None),
    ("dcsa", "dcsa", "dcsa", None),
    ("dcp", "dcp", "dcp", None),
    ("dcpf", "dcpf", "dcpf", None),
]


def parse_args():
    p = argparse.ArgumentParser(description="Verify ETL data integrity across XML, MongoDB, Neo4j")
    p.add_argument("--skip-xml", action="store_true",
                   help="Skip XML parsing (compare only MongoDB vs Neo4j)")
    p.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
    return p.parse_args()


def status(ok, warn=False):
    return "PASS" if ok else ("WARN" if warn else "FAIL")


# -------------------------------------------------------------------------
# 1. SOURCE OF TRUTH: XML
# -------------------------------------------------------------------------
def read_xml_truth(settings):
    """Stream Prescripcion.xml for drug/interaction truth; use extractors for dicts."""
    presc = settings.xml_files["prescripcion"]
    logger.info(f"Parsing source XML: {presc} (streamed)...")

    drug_count = 0
    interaction_raw = 0
    distinct_pairs = set()
    duplicity_count = 0
    biomarker_count = 0

    for _, elem in ET.iterparse(presc, events=("end",)):
        if elem.tag == NS + "prescription":
            drug_count += 1
            cod = elem.findtext(NS + "cod_nacion", default="")
            atc_elem = elem.find(NS + "atc")
            if atc_elem is not None:
                for inter in atc_elem.findall(NS + "interacciones_atc"):
                    t = (inter.findtext(NS + "atc_interaccion", default="") or "").strip()
                    if t:
                        interaction_raw += 1
                        distinct_pairs.add((cod, t))
                duplicity_count += len(atc_elem.findall(NS + "duplicidades"))
            biomarker_count += len(elem.findall(NS + "biomarcadores"))
            elem.clear()

    logger.info("Counting reference dictionaries...")
    ref = DictionaryExtractor(settings.xml_files).extract_all()
    ref_counts = {k: len(v) for k, v in ref.items()}

    return {
        "drugs": drug_count,
        "interactions_raw": interaction_raw,
        "interactions_distinct_pairs": len(distinct_pairs),
        "interactions_duplicate_rows": interaction_raw - len(distinct_pairs),
        "duplicities": duplicity_count,
        "biomarkers": biomarker_count,
        "reference": ref_counts,
    }


# -------------------------------------------------------------------------
# 2. MONGODB
# -------------------------------------------------------------------------
def read_mongo(settings):
    m = MongoClient(settings.mongodb_uri)
    db = m[settings.mongodb_db]
    try:
        out = {
            "drugs": db["drugs"].count_documents({}),
            "drug_interactions": db["drug_interactions"].count_documents({}),
            "reference": {},
            "referential": {},
        }
        for label, _, coll, _ in REFERENCE_MAP:
            out["reference"][label] = db[coll].count_documents({})

        # Referential integrity: interactions whose origin drug exists
        drug_codes = set(db["drugs"].distinct("cod_nacion"))
        origin_codes = set(db["drug_interactions"].distinct("medicamento_origen.cod_nacion"))
        out["referential"]["interactions_with_missing_origin_drug"] = len(origin_codes - drug_codes)

        # Interactions whose target ATC exists as a reference code
        atc_codes = set(db["atc_codes"].distinct("codigo"))
        target_codes = set(db["drug_interactions"].distinct("medicamento_destino.atc"))
        out["referential"]["target_atc_codes_not_in_dictionary"] = len(target_codes - atc_codes)
        return out
    finally:
        m.close()


# -------------------------------------------------------------------------
# 3. NEO4J
# -------------------------------------------------------------------------
def read_neo4j(settings):
    d = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    try:
        with d.session() as s:
            def one(q):
                return s.run(q).single()[0]

            out = {
                "nodes": {
                    "Drug": one("MATCH (n:Drug) RETURN count(n)"),
                },
                "relationships": {
                    "INTERACTS_WITH_ATC": one("MATCH ()-[r:INTERACTS_WITH_ATC]->() RETURN count(r)"),
                    "CLASSIFIED_AS": one("MATCH ()-[r:CLASSIFIED_AS]->() RETURN count(r)"),
                    "MANUFACTURED_BY": one("MATCH ()-[r:MANUFACTURED_BY]->() RETURN count(r)"),
                    "CONTAINS": one("MATCH ()-[r:CONTAINS]->() RETURN count(r)"),
                },
                "reference": {},
                "referential": {},
            }
            for label, _, _, neo_label in REFERENCE_MAP:
                if neo_label:
                    out["reference"][label] = one(f"MATCH (n:{neo_label}) RETURN count(n)")

            # Referential integrity: every INTERACTS_WITH_ATC must end on an ATCCode
            out["referential"]["interacts_edges_with_non_atc_target"] = one(
                "MATCH ()-[r:INTERACTS_WITH_ATC]->(t) WHERE NOT t:ATCCode RETURN count(r)"
            )
            # Drug nodes pointing at a missing ATC via CLASSIFIED_AS cannot exist (MATCH-created),
            # but verify there are no duplicate Drug cod_nacion (constraint should guarantee).
            out["referential"]["duplicate_drug_cod_nacion"] = one(
                "MATCH (d:Drug) WITH d.cod_nacion AS c, count(*) AS n WHERE n>1 RETURN count(c)"
            )
            return out
    finally:
        d.close()


# -------------------------------------------------------------------------
# Reconciliation + report
# -------------------------------------------------------------------------
def main():
    args = parse_args()
    global logger
    logger = setup_logging(args.log_level)
    settings = get_settings()

    logger.info("=" * 66)
    logger.info("ETL DATA INTEGRITY VERIFICATION")
    logger.info("=" * 66)

    xml = None if args.skip_xml else read_xml_truth(settings)
    mongo = read_mongo(settings)
    neo = read_neo4j(settings)

    checks = []  # (name, status, detail)

    # --- Core entity reconciliation ---
    if xml:
        checks.append(("Drugs: XML == MongoDB",
                       status(xml["drugs"] == mongo["drugs"]),
                       f"XML={xml['drugs']:,}  Mongo={mongo['drugs']:,}"))
        checks.append(("Drugs: XML == Neo4j",
                       status(xml["drugs"] == neo["nodes"]["Drug"]),
                       f"XML={xml['drugs']:,}  Neo4j={neo['nodes']['Drug']:,}"))
        checks.append(("Interactions: XML raw == MongoDB docs",
                       status(xml["interactions_raw"] == mongo["drug_interactions"]),
                       f"XML={xml['interactions_raw']:,}  Mongo={mongo['drug_interactions']:,}"))
        checks.append(("Interactions: XML distinct pairs == Neo4j edges",
                       status(xml["interactions_distinct_pairs"] == neo["relationships"]["INTERACTS_WITH_ATC"]),
                       f"XML_distinct={xml['interactions_distinct_pairs']:,}  "
                       f"Neo4j={neo['relationships']['INTERACTS_WITH_ATC']:,}"))
    else:
        checks.append(("Drugs: MongoDB == Neo4j",
                       status(mongo["drugs"] == neo["nodes"]["Drug"]),
                       f"Mongo={mongo['drugs']:,}  Neo4j={neo['nodes']['Drug']:,}"))

    # --- The documented dedup explanation ---
    raw = xml["interactions_raw"] if xml else mongo["drug_interactions"]
    distinct = (xml["interactions_distinct_pairs"] if xml
                else neo["relationships"]["INTERACTS_WITH_ATC"])
    dup = raw - distinct
    checks.append(("Interaction dedup is fully explained",
                   status(mongo["drug_interactions"] - neo["relationships"]["INTERACTS_WITH_ATC"] == dup, warn=True),
                   f"MongoDB raw={mongo['drug_interactions']:,}  "
                   f"Neo4j unique={neo['relationships']['INTERACTS_WITH_ATC']:,}  "
                   f"duplicate (drug,ATC) rows collapsed={dup:,}"))

    # --- Reference dictionary reconciliation ---
    for label, _, _, neo_label in REFERENCE_MAP:
        xml_n = xml["reference"].get(label) if xml else None
        mongo_n = mongo["reference"].get(label)
        neo_n = neo["reference"].get(label)
        parts = []
        ok = True
        if xml_n is not None:
            parts.append(f"XML={xml_n:,}")
            ok = ok and (xml_n == mongo_n)
        parts.append(f"Mongo={mongo_n:,}")
        if neo_n is not None:
            parts.append(f"Neo4j={neo_n:,}")
            ok = ok and (mongo_n == neo_n)
        checks.append((f"Reference '{label}'", status(ok), "  ".join(parts)))

    # --- Referential integrity ---
    checks.append(("Mongo: interactions reference an existing origin drug",
                   status(mongo["referential"]["interactions_with_missing_origin_drug"] == 0),
                   f"missing={mongo['referential']['interactions_with_missing_origin_drug']}"))
    checks.append(("Mongo: target ATC codes exist in dictionary",
                   status(mongo["referential"]["target_atc_codes_not_in_dictionary"] == 0, warn=True),
                   f"missing={mongo['referential']['target_atc_codes_not_in_dictionary']}"))
    checks.append(("Neo4j: all INTERACTS_WITH_ATC end on an ATCCode",
                   status(neo["referential"]["interacts_edges_with_non_atc_target"] == 0),
                   f"violations={neo['referential']['interacts_edges_with_non_atc_target']}"))
    checks.append(("Neo4j: Drug.cod_nacion is unique",
                   status(neo["referential"]["duplicate_drug_cod_nacion"] == 0),
                   f"duplicates={neo['referential']['duplicate_drug_cod_nacion']}"))

    # --- Print report ---
    print()
    print("=" * 78)
    print(" ETL INTEGRITY REPORT")
    print("=" * 78)
    width = max(len(n) for n, _, _ in checks)
    n_pass = n_warn = n_fail = 0
    for name, st, detail in checks:
        if st == "PASS":
            n_pass += 1
        elif st == "WARN":
            n_warn += 1
        else:
            n_fail += 1
        print(f"  [{st:4}] {name.ljust(width)}  | {detail}")
    print("-" * 78)
    print(f"  {n_pass} PASS, {n_warn} WARN, {n_fail} FAIL")
    print("=" * 78)

    # --- Save JSON report ---
    results_dir = Path(__file__).resolve().parents[1] / "results"
    results_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = results_dir / f"integrity_report_{stamp}.json"
    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": {"pass": n_pass, "warn": n_warn, "fail": n_fail},
        "checks": [{"name": n, "status": s, "detail": d} for n, s, d in checks],
        "xml": xml,
        "mongodb": mongo,
        "neo4j": neo,
    }
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Report written to {report_path}")

    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
