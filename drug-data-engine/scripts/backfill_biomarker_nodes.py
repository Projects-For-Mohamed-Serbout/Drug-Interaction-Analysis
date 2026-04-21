"""
Backfill Biomarker nodes and HAS_BIOMARKER relationships in Neo4j.

Biomarker data is embedded in each drug in Prescripcion.xml (not a separate
dictionary). This script extracts unique biomarkers, creates Biomarker nodes,
and links them to Drug nodes via HAS_BIOMARKER relationships.

Usage:
    python scripts/backfill_biomarker_nodes.py
    python scripts/backfill_biomarker_nodes.py --dry-run
"""
import argparse
import logging
from neo4j import GraphDatabase

from src.config import get_settings
from src.utils import setup_logging
from src.extractors import PrescriptionExtractor
from src.transformers import DataTransformer
from src.extractors import DictionaryExtractor


def parse_args():
    parser = argparse.ArgumentParser(
        description='Backfill Biomarker nodes and HAS_BIOMARKER relationships'
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview without writing to Neo4j')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING'],
                        default='INFO')
    return parser.parse_args()


def main():
    args = parse_args()
    logger = setup_logging(args.log_level)

    settings = get_settings()

    logger.info("=" * 60)
    logger.info("BACKFILL: Biomarker nodes + HAS_BIOMARKER relationships")
    logger.info("=" * 60)

    # --- Step 1: Check current state ---
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password)
    )
    driver.verify_connectivity()
    logger.info("Connected to Neo4j")

    with driver.session() as session:
        r = session.run("MATCH (b:Biomarker) RETURN count(b) AS c").single()
        existing_nodes = r['c']
        logger.info(f"Existing Biomarker nodes: {existing_nodes}")

        try:
            r = session.run(
                "MATCH ()-[r:HAS_BIOMARKER]->() RETURN count(r) AS c"
            ).single()
            existing_rels = r['c']
        except Exception:
            existing_rels = 0
        logger.info(f"Existing HAS_BIOMARKER relationships: {existing_rels}")

    # --- Step 2: Fix constraint (old was on .nombre, should be .marcador) ---
    logger.info("Ensuring correct constraint on Biomarker.marcador...")
    with driver.session() as session:
        try:
            session.run(
                "DROP CONSTRAINT biomarker_nombre IF EXISTS"
            )
        except Exception:
            pass
        try:
            session.run(
                "CREATE CONSTRAINT biomarker_marcador IF NOT EXISTS "
                "FOR (b:Biomarker) REQUIRE b.marcador IS UNIQUE"
            )
            logger.info("Constraint biomarker_marcador ensured")
        except Exception as e:
            logger.warning(f"Constraint already exists or error: {e}")

    # --- Step 3: Extract biomarker data from XML ---
    logger.info("")
    logger.info("Extracting data from XML sources...")

    dict_extractor = DictionaryExtractor(settings.xml_files)
    reference_data = dict_extractor.extract_all()

    presc_extractor = PrescriptionExtractor(settings.xml_files['prescripcion'])
    drugs = list(presc_extractor.extract_drugs())
    logger.info(f"Extracted {len(drugs)} drugs from Prescripcion.xml")

    transformer = DataTransformer(reference_data)

    # Collect unique biomarkers and drug-biomarker relationships
    unique_biomarkers = {}
    relationships = []

    for drug in drugs:
        neo4j_data = transformer.transform_drug_for_neo4j(drug)
        cod_nacion = neo4j_data['node']['cod_nacion']

        for bio in neo4j_data['relationships']['biomarkers']:
            marcador = bio['marcador']
            if not marcador:
                continue

            # Track unique biomarkers
            if marcador not in unique_biomarkers:
                unique_biomarkers[marcador] = {
                    'marcador': marcador,
                    'clase': bio.get('clase', ''),
                }

            # Track relationship
            relationships.append({
                'cod_nacion': cod_nacion,
                'marcador': marcador,
                'genotipo_fenotipo': bio.get('genotipo_fenotipo'),
                'notas': bio.get('notas'),
            })

    logger.info(f"Found {len(unique_biomarkers)} unique biomarkers")
    logger.info(f"Found {len(relationships)} drug-biomarker relationships")

    drugs_with_biomarkers = len(set(r['cod_nacion'] for r in relationships))
    logger.info(f"  Covering {drugs_with_biomarkers} drugs")

    if args.dry_run:
        logger.info("")
        logger.info("DRY RUN -- no changes written to Neo4j")
        logger.info("Sample biomarkers:")
        for name, bio in list(unique_biomarkers.items())[:10]:
            logger.info(f"  {bio['marcador']} (clase: {bio['clase']})")
        logger.info("Sample relationships:")
        for r in relationships[:5]:
            logger.info(
                f"  Drug({r['cod_nacion']}) -[:HAS_BIOMARKER]-> "
                f"Biomarker({r['marcador']})"
            )
        driver.close()
        return

    # --- Step 4: Create Biomarker nodes ---
    logger.info("")
    logger.info("Creating Biomarker nodes...")

    biomarker_list = list(unique_biomarkers.values())
    node_query = """
    UNWIND $batch AS item
    MERGE (b:Biomarker {marcador: item.marcador})
    SET b.clase = item.clase
    """

    batch_size = 100
    with driver.session() as session:
        for i in range(0, len(biomarker_list), batch_size):
            batch = biomarker_list[i:i + batch_size]
            session.run(node_query, batch=batch)
    logger.info(f"Created/updated {len(biomarker_list)} Biomarker nodes")

    # --- Step 5: Create HAS_BIOMARKER relationships ---
    logger.info("Creating HAS_BIOMARKER relationships...")

    rel_query = """
    UNWIND $batch AS item
    MATCH (d:Drug {cod_nacion: item.cod_nacion})
    MATCH (b:Biomarker {marcador: item.marcador})
    MERGE (d)-[r:HAS_BIOMARKER]->(b)
    SET r.genotipo_fenotipo = item.genotipo_fenotipo,
        r.notas = item.notas
    """

    batch_size = 500
    created = 0
    with driver.session() as session:
        for i in range(0, len(relationships), batch_size):
            batch = relationships[i:i + batch_size]
            session.run(rel_query, batch=batch)
            created += len(batch)
            if created % 2000 == 0 or created == len(relationships):
                logger.info(f"  Processed {created}/{len(relationships)} relationships")

    # --- Step 6: Verify ---
    logger.info("")
    logger.info("Verifying...")
    with driver.session() as session:
        r = session.run("MATCH (b:Biomarker) RETURN count(b) AS c").single()
        final_nodes = r['c']

        r = session.run(
            "MATCH ()-[r:HAS_BIOMARKER]->() RETURN count(r) AS c"
        ).single()
        final_rels = r['c']

        r = session.run(
            "MATCH (d:Drug)-[:HAS_BIOMARKER]->() "
            "RETURN count(DISTINCT d) AS drugs"
        ).single()
        drugs_linked = r['drugs']

        # Show clase distribution
        results = session.run(
            "MATCH (b:Biomarker) "
            "RETURN b.clase AS clase, count(b) AS count "
            "ORDER BY count DESC"
        )
        clase_dist = [(r['clase'], r['count']) for r in results]

    logger.info(f"Biomarker nodes: {existing_nodes} -> {final_nodes}")
    logger.info(f"HAS_BIOMARKER relationships: {existing_rels} -> {final_rels}")
    logger.info(f"Drugs with biomarker links: {drugs_linked}")
    logger.info("")
    logger.info("Biomarker classes:")
    for clase, count in clase_dist:
        logger.info(f"  {clase}: {count}")
    logger.info("")
    logger.info("Backfill complete!")

    driver.close()


if __name__ == '__main__':
    main()
