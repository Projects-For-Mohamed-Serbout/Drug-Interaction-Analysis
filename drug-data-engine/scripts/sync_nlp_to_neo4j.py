"""
Sync NLP Results from MongoDB to Neo4J.

This script reads NLP-classified fields (severity, type, mechanism) from MongoDB
and updates the corresponding INTERACTS_WITH_ATC relationships in Neo4J.

Usage:
    python sync_nlp_to_neo4j.py
    python sync_nlp_to_neo4j.py --batch-size 1000
    python sync_nlp_to_neo4j.py --dry-run
"""
import argparse
import logging
from typing import Dict, List
from pymongo import MongoClient
from neo4j import GraphDatabase
from tqdm import tqdm

from src.config import get_settings
from src.utils import setup_logging


logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Sync NLP results from MongoDB to Neo4J'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=500,
        help='Number of interactions to process per batch (default: 500)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without updating Neo4J'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    return parser.parse_args()


def fetch_nlp_results(mongo_client: MongoClient, db_name: str, batch_size: int) -> List[Dict]:
    """Fetch NLP results from MongoDB."""
    logger.info("Fetching NLP results from MongoDB...")

    db = mongo_client[db_name]
    collection = db['drug_interactions']

    # Only fetch interactions that have NLP results
    # NLP data is nested under interaccion.nlp
    cursor = collection.find(
        {'interaccion.nlp': {'$exists': True}},
        {
            'medicamento_origen.cod_nacion': 1,
            'medicamento_destino.atc': 1,
            'interaccion.nlp.severidad': 1,
            'interaccion.nlp.tipo': 1,
            'interaccion.nlp.mecanismo': 1
        }
    ).batch_size(batch_size)

    interactions = list(cursor)
    logger.info(f"Found {len(interactions)} interactions with NLP results")

    return interactions


def update_neo4j_relationship(tx, cod_origen: str, atc_destino: str, nlp_data: Dict):
    """Update a single Neo4J relationship with NLP data."""
    # In Neo4j, interactions are by ATC code, not cod_nacion
    query = """
    MATCH (d1:Drug {cod_nacion: $cod_origen})-[i:INTERACTS_WITH_ATC]->(atc:ATCCode {codigo: $atc_destino})
    SET i.severidad = $severidad,
        i.tipo = $tipo,
        i.mecanismo = $mecanismo
    RETURN i
    """

    result = tx.run(query, {
        'cod_origen': cod_origen,
        'atc_destino': atc_destino,
        'severidad': nlp_data.get('severidad'),
        'tipo': nlp_data.get('tipo'),
        'mecanismo': nlp_data.get('mecanismo')
    })

    return result.single() is not None


def sync_to_neo4j(driver, interactions: List[Dict], dry_run: bool = False) -> Dict:
    """Sync NLP results to Neo4J relationships."""
    stats = {
        'total': len(interactions),
        'updated': 0,
        'not_found': 0,
        'errors': 0
    }

    logger.info(f"{'DRY RUN: ' if dry_run else ''}Syncing {stats['total']} interactions to Neo4J...")

    with driver.session() as session:
        for interaction in tqdm(interactions, desc="Syncing"):
            try:
                # Extract data from MongoDB structure
                cod_origen = interaction.get('medicamento_origen', {}).get('cod_nacion')
                atc_destino = interaction.get('medicamento_destino', {}).get('atc')
                nlp_data = interaction.get('interaccion', {}).get('nlp', {})

                if not cod_origen or not atc_destino:
                    logger.warning(f"Missing cod_origen or atc_destino: {interaction.get('_id')}")
                    stats['errors'] += 1
                    continue

                if dry_run:
                    logger.debug(f"DRY RUN: Would update {cod_origen} -> {atc_destino} with {nlp_data}")
                    stats['updated'] += 1
                else:
                    # Update in transaction
                    updated = session.execute_write(
                        update_neo4j_relationship,
                        cod_origen,
                        atc_destino,
                        nlp_data
                    )

                    if updated:
                        stats['updated'] += 1
                    else:
                        stats['not_found'] += 1
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.warning(f"Relationship not found: {cod_origen} -> {atc_destino}")

            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Error updating {cod_origen} -> {atc_destino}: {e}")

    return stats


def verify_sync(driver) -> Dict:
    """Verify that NLP fields exist in Neo4J relationships."""
    logger.info("Verifying sync results...")

    query = """
    MATCH ()-[i:INTERACTS_WITH_ATC]->()
    RETURN
        count(*) AS total_interactions,
        count(i.severidad) AS with_severidad,
        count(i.tipo) AS with_tipo,
        count(i.mecanismo) AS with_mecanismo
    """

    with driver.session() as session:
        result = session.run(query).single()

        verification = {
            'total_interactions': result['total_interactions'],
            'with_severidad': result['with_severidad'],
            'with_tipo': result['with_tipo'],
            'with_mecanismo': result['with_mecanismo']
        }

        return verification


def print_stats(stats: Dict, verification: Dict = None):
    """Print sync statistics."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("SYNC STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Total interactions processed: {stats['total']}")
    logger.info(f"Successfully updated: {stats['updated']}")
    logger.info(f"Not found in Neo4J: {stats['not_found']}")
    logger.info(f"Errors: {stats['errors']}")

    if verification:
        logger.info("")
        logger.info("VERIFICATION RESULTS")
        logger.info("-" * 60)
        logger.info(f"Total relationships in Neo4J: {verification['total_interactions']}")
        logger.info(f"With severidad field: {verification['with_severidad']}")
        logger.info(f"With tipo field: {verification['with_tipo']}")
        logger.info(f"With mecanismo field: {verification['with_mecanismo']}")

        coverage = (verification['with_severidad'] / verification['total_interactions'] * 100) if verification['total_interactions'] > 0 else 0
        logger.info(f"Coverage: {coverage:.1f}%")

    logger.info("=" * 60)


def main():
    """Main entry point."""
    args = parse_args()
    logger = setup_logging(args.log_level)

    logger.info("=" * 60)
    logger.info("SYNC NLP RESULTS: MongoDB -> Neo4J")
    logger.info("=" * 60)

    if args.dry_run:
        logger.warning("DRY RUN MODE: No changes will be made to Neo4J")

    # Load settings
    settings = get_settings()

    # Connect to MongoDB
    logger.info(f"Connecting to MongoDB...")
    mongo_client = MongoClient(settings.mongodb_uri)

    # Connect to Neo4J
    logger.info(f"Connecting to Neo4J...")
    neo4j_driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password)
    )

    try:
        # Test connections
        mongo_client.admin.command('ping')
        neo4j_driver.verify_connectivity()
        logger.info("Successfully connected to both databases")

        # Fetch NLP results from MongoDB
        interactions = fetch_nlp_results(
            mongo_client,
            settings.mongodb_db,
            args.batch_size
        )

        if not interactions:
            logger.warning("No interactions with NLP results found!")
            return

        # Sync to Neo4J
        stats = sync_to_neo4j(neo4j_driver, interactions, dry_run=args.dry_run)

        # Verify sync (only if not dry run)
        verification = None
        if not args.dry_run:
            verification = verify_sync(neo4j_driver)

        # Print results
        print_stats(stats, verification)

        logger.info("")
        logger.info("Sync complete!")

    except Exception as e:
        logger.error(f"Error during sync: {e}", exc_info=True)
        raise
    finally:
        mongo_client.close()
        neo4j_driver.close()


if __name__ == '__main__':
    main()
