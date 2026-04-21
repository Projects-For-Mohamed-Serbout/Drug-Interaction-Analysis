"""
Backfill CONTAINS_EXCIPIENT relationships in Neo4j.

This script re-extracts excipient data from the XML source and creates
the missing CONTAINS_EXCIPIENT relationships between Drug and Excipient
nodes that already exist in Neo4j.

Usage:
    python scripts/backfill_excipient_relationships.py
    python scripts/backfill_excipient_relationships.py --dry-run
"""
import argparse
import logging
from neo4j import GraphDatabase

from src.config import get_settings
from src.utils import setup_logging
from src.extractors import DictionaryExtractor, PrescriptionExtractor
from src.transformers import DataTransformer


def parse_args():
    parser = argparse.ArgumentParser(
        description='Backfill CONTAINS_EXCIPIENT relationships in Neo4j'
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

    # --- Step 1: Check current state of Neo4j ---
    logger.info("=" * 60)
    logger.info("BACKFILL: CONTAINS_EXCIPIENT relationships")
    logger.info("=" * 60)

    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password)
    )
    driver.verify_connectivity()
    logger.info("Connected to Neo4j")

    with driver.session() as session:
        # Check Excipient nodes exist
        r = session.run("MATCH (e:Excipient) RETURN count(e) AS c").single()
        excipient_nodes = r['c']
        logger.info(f"Excipient nodes in Neo4j: {excipient_nodes}")

        if excipient_nodes == 0:
            logger.error("No Excipient nodes found. Run the full ETL first.")
            driver.close()
            return

        # Check existing relationships
        r = session.run(
            "MATCH ()-[r:CONTAINS_EXCIPIENT]->() RETURN count(r) AS c"
        ).single()
        existing_rels = r['c']
        logger.info(f"Existing CONTAINS_EXCIPIENT relationships: {existing_rels}")

        r = session.run("MATCH (d:Drug) RETURN count(d) AS c").single()
        drug_count = r['c']
        logger.info(f"Drug nodes: {drug_count}")

    # --- Step 2: Extract excipient data from XML ---
    logger.info("")
    logger.info("Extracting data from XML sources...")

    dict_extractor = DictionaryExtractor(settings.xml_files)
    reference_data = dict_extractor.extract_all()

    presc_extractor = PrescriptionExtractor(settings.xml_files['prescripcion'])
    drugs = list(presc_extractor.extract_drugs())
    logger.info(f"Extracted {len(drugs)} drugs from Prescripcion.xml")

    # --- Step 3: Transform to get excipient relationships ---
    transformer = DataTransformer(reference_data)

    # Collect all (drug_cod_nacion, excipient_code) pairs
    relationships = []
    for drug in drugs:
        neo4j_data = transformer.transform_drug_for_neo4j(drug)
        cod_nacion = neo4j_data['node']['cod_nacion']
        excipient_codes = neo4j_data['relationships']['contains_excipient']
        for exc_code in excipient_codes:
            relationships.append({
                'cod_nacion': cod_nacion,
                'exc_code': exc_code
            })

    logger.info(f"Found {len(relationships)} drug-excipient relationships to create")

    drugs_with_excipients = len(set(r['cod_nacion'] for r in relationships))
    unique_excipients = len(set(r['exc_code'] for r in relationships))
    logger.info(f"  Covering {drugs_with_excipients} drugs and {unique_excipients} excipients")

    if args.dry_run:
        logger.info("")
        logger.info("DRY RUN — no changes written to Neo4j")
        # Show a sample
        for r in relationships[:5]:
            logger.info(f"  Would create: Drug({r['cod_nacion']}) -[:CONTAINS_EXCIPIENT]-> Excipient({r['exc_code']})")
        driver.close()
        return

    # --- Step 4: Write relationships in batches ---
    logger.info("")
    logger.info("Writing CONTAINS_EXCIPIENT relationships to Neo4j...")

    query = """
    UNWIND $batch AS item
    MATCH (d:Drug {cod_nacion: item.cod_nacion})
    MATCH (e:Excipient {codigo: item.exc_code})
    MERGE (d)-[:CONTAINS_EXCIPIENT]->(e)
    """

    batch_size = 500
    created = 0
    with driver.session() as session:
        for i in range(0, len(relationships), batch_size):
            batch = relationships[i:i + batch_size]
            session.run(query, batch=batch)
            created += len(batch)
            if created % 5000 == 0 or created == len(relationships):
                logger.info(f"  Processed {created}/{len(relationships)} relationships")

    # --- Step 5: Verify ---
    logger.info("")
    logger.info("Verifying...")
    with driver.session() as session:
        r = session.run(
            "MATCH ()-[r:CONTAINS_EXCIPIENT]->() RETURN count(r) AS c"
        ).single()
        final_count = r['c']

        r = session.run(
            "MATCH (d:Drug)-[:CONTAINS_EXCIPIENT]->() "
            "RETURN count(DISTINCT d) AS drugs"
        ).single()
        drugs_linked = r['drugs']

        r = session.run(
            "MATCH ()-[:CONTAINS_EXCIPIENT]->(e:Excipient) "
            "RETURN count(DISTINCT e) AS excipients"
        ).single()
        excipients_linked = r['excipients']

    logger.info(f"CONTAINS_EXCIPIENT relationships: {existing_rels} -> {final_count}")
    logger.info(f"Drugs with excipient links: {drugs_linked}")
    logger.info(f"Excipients referenced: {excipients_linked}")
    logger.info("")
    logger.info("Backfill complete!")

    driver.close()


if __name__ == '__main__':
    main()
