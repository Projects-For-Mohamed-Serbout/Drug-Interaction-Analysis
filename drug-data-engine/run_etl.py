"""
Main ETL Pipeline for Drug Interaction Data.

This script orchestrates the complete ETL process:
1. Extract data from CIMA XML files
2. Transform data for MongoDB and Neo4J
3. Load data into both databases

Usage:
    python run_etl.py                    # Run full ETL
    python run_etl.py --mongodb-only     # Load only to MongoDB
    python run_etl.py --neo4j-only       # Load only to Neo4J
    python run_etl.py --clear            # Clear databases before loading
    python run_etl.py --test             # Test extraction only (no loading)
"""
import argparse
import sys
import time
from datetime import datetime
from typing import List, Dict

from src.config import get_settings
from src.utils import setup_logging
from src.extractors import DictionaryExtractor, PrescriptionExtractor
from src.transformers import DataTransformer
from src.loaders import MongoDBLoader, Neo4JLoader


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Drug Interaction ETL Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--mongodb-only',
        action='store_true',
        help='Load only to MongoDB'
    )
    parser.add_argument(
        '--neo4j-only',
        action='store_true',
        help='Load only to Neo4J'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear databases before loading'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test extraction only (no database loading)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )

    return parser.parse_args()


def extract_reference_data(settings, logger) -> Dict:
    """Extract all reference/dictionary data."""
    logger.info("=" * 60)
    logger.info("PHASE 1: Extracting reference data from dictionaries")
    logger.info("=" * 60)

    extractor = DictionaryExtractor(settings.xml_files)
    reference_data = extractor.extract_all()

    # Log summary
    for name, data in reference_data.items():
        logger.info(f"  {name}: {len(data)} records")

    return reference_data


def extract_drugs(settings, logger):
    """Extract drugs from prescription file."""
    logger.info("=" * 60)
    logger.info("PHASE 2: Extracting drugs from Prescripcion.xml")
    logger.info("=" * 60)

    extractor = PrescriptionExtractor(settings.xml_files['prescripcion'])
    drugs = list(extractor.extract_drugs())

    logger.info(f"Extracted {len(drugs)} drugs")
    logger.info(f"Extracted {extractor.interactions_count} drug interactions")

    return drugs


def load_to_mongodb(settings, reference_data, drugs, transformer, clear: bool, logger):
    """Load data to MongoDB."""
    logger.info("=" * 60)
    logger.info("PHASE 3a: Loading data to MongoDB")
    logger.info("=" * 60)

    loader = MongoDBLoader(settings.mongodb_uri, settings.mongodb_db)

    if not loader.connect():
        logger.error("Failed to connect to MongoDB. Aborting.")
        return False

    try:
        if clear:
            logger.info("Clearing existing MongoDB collections...")
            loader.clear_all_collections()

        # Setup indexes
        loader.setup_collections()

        # Load reference data
        logger.info("Loading reference data...")
        for name, collection_name in [
            ('active_ingredients', 'active_ingredients'),
            ('laboratories', 'laboratories'),
            ('atc_codes', 'atc_codes'),
            ('pharmaceutical_forms', 'pharmaceutical_forms'),
            ('simplified_pharmaceutical_forms', 'simplified_pharmaceutical_forms'),
            ('administration_routes', 'administration_routes'),
            ('excipients', 'excipients'),
            ('package_types', 'package_types'),
            ('content_units', 'content_units'),
            ('registration_statuses', 'registration_statuses'),
            ('dcsa', 'dcsa'),
            ('dcp', 'dcp'),
            ('dcpf', 'dcpf')
        ]:
            data = transformer.transform_reference_for_mongodb(name)
            if data:
                loader.insert_many(collection_name, data)

        # Load drugs
        logger.info("Loading drugs...")
        drug_docs = []
        interaction_docs = []

        for drug in drugs:
            drug_doc = transformer.transform_drug_for_mongodb(drug)
            drug_docs.append(drug_doc)

            # Extract interactions for separate collection
            interactions = transformer.extract_interactions_for_mongodb(drug)
            interaction_docs.extend(interactions)

        loader.insert_many('drugs', drug_docs)
        logger.info(f"Loaded {len(drug_docs)} drugs")

        if interaction_docs:
            loader.insert_many('drug_interactions', interaction_docs)
            logger.info(f"Loaded {len(interaction_docs)} interactions to drug_interactions collection")

        # Print stats
        stats = loader.get_stats()
        logger.info("MongoDB collection counts:")
        for name, count in stats.items():
            logger.info(f"  {name}: {count}")

        return True

    finally:
        loader.disconnect()


def load_to_neo4j(settings, reference_data, drugs, transformer, clear: bool, logger):
    """Load data to Neo4J."""
    logger.info("=" * 60)
    logger.info("PHASE 3b: Loading data to Neo4J")
    logger.info("=" * 60)

    loader = Neo4JLoader(
        settings.neo4j_uri,
        settings.neo4j_user,
        settings.neo4j_password
    )

    if not loader.connect():
        logger.error("Failed to connect to Neo4J. Aborting.")
        return False

    try:
        if clear:
            logger.info("Clearing existing Neo4J database...")
            loader.clear_database()

        # Setup constraints and indexes
        loader.setup_constraints_and_indexes()

        # Load reference nodes
        logger.info("Loading reference nodes...")

        loader.load_active_ingredients(
            transformer.transform_reference_for_mongodb('active_ingredients')
        )
        loader.load_laboratories(
            transformer.transform_reference_for_mongodb('laboratories')
        )
        loader.load_atc_codes(
            transformer.transform_reference_for_mongodb('atc_codes')
        )
        loader.load_pharmaceutical_forms(
            transformer.transform_reference_for_mongodb('pharmaceutical_forms')
        )
        loader.load_administration_routes(
            transformer.transform_reference_for_mongodb('administration_routes')
        )
        loader.load_excipients(
            transformer.transform_reference_for_mongodb('excipients')
        )
        loader.load_package_types(
            transformer.transform_reference_for_mongodb('package_types')
        )

        # Load ATC hierarchy
        hierarchy = transformer.build_atc_hierarchy()
        loader.load_atc_hierarchy(hierarchy)

        # Transform and load drugs
        logger.info("Transforming drugs for Neo4J...")
        drug_data = [transformer.transform_drug_for_neo4j(drug) for drug in drugs]

        loader.load_drugs(drug_data)
        loader.load_biomarkers(drug_data)
        loader.load_drug_relationships(drug_data)
        loader.load_drug_interactions(drug_data)

        # Print stats
        stats = loader.get_stats()
        logger.info("Neo4J counts:")
        for name, count in stats.items():
            logger.info(f"  {name}: {count}")

        return True

    finally:
        loader.disconnect()


def main():
    """Main entry point."""
    args = parse_args()
    logger = setup_logging(args.log_level)

    start_time = time.time()

    logger.info("=" * 60)
    logger.info("DRUG INTERACTION ETL PIPELINE")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # Load settings
    settings = get_settings()

    # Validate settings
    if not settings.validate():
        logger.error("Configuration validation failed. Please check your .env file.")
        sys.exit(1)

    logger.info(f"Data directory: {settings.data_dir}")
    logger.info(f"MongoDB database: {settings.mongodb_db}")
    logger.info(f"Neo4J URI: {settings.neo4j_uri}")

    # Extract reference data
    reference_data = extract_reference_data(settings, logger)

    # Extract drugs
    drugs = extract_drugs(settings, logger)

    if args.test:
        logger.info("Test mode - skipping database loading")
        logger.info(f"Would load {len(drugs)} drugs")
        total_interactions = sum(
            len(d.atc.interacciones) if d.atc else 0 for d in drugs
        )
        logger.info(f"Would load {total_interactions} interactions")
    else:
        # Create transformer
        transformer = DataTransformer(reference_data)

        load_mongodb = not args.neo4j_only
        load_neo4j = not args.mongodb_only

        # Load to MongoDB
        if load_mongodb:
            mongodb_success = load_to_mongodb(
                settings, reference_data, drugs, transformer, args.clear, logger
            )
            if not mongodb_success:
                logger.error("MongoDB loading failed")

        # Load to Neo4J
        if load_neo4j:
            neo4j_success = load_to_neo4j(
                settings, reference_data, drugs, transformer, args.clear, logger
            )
            if not neo4j_success:
                logger.error("Neo4J loading failed")

    # Summary
    elapsed_time = time.time() - start_time
    logger.info("=" * 60)
    logger.info("ETL PIPELINE COMPLETED")
    logger.info(f"Total time: {elapsed_time:.2f} seconds")
    logger.info(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
