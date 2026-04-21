"""
NLP Processing Script for Drug Interactions.

Processes all drug interactions in MongoDB with NLP analysis
to extract severity, type, and mechanism information.

Usage:
    python run_nlp.py                    # Process all unprocessed interactions
    python run_nlp.py --reprocess        # Reprocess all interactions
    python run_nlp.py --sample 100       # Process only 100 interactions (test)
    python run_nlp.py --stats            # Show statistics only
"""
import argparse
import sys
import time
from datetime import datetime
import logging

from src.config import get_settings
from src.utils import setup_logging
from src.loaders import MongoDBLoader
from src.nlp import NLPPipeline


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='NLP Processing for Drug Interactions',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--reprocess',
        action='store_true',
        help='Reprocess all interactions (ignore previous processing)'
    )
    parser.add_argument(
        '--sample',
        type=int,
        default=0,
        help='Process only N interactions (for testing)'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics only, do not process'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Batch size for processing (default: 1000)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )

    return parser.parse_args()


def get_interactions_to_process(db, reprocess: bool, sample: int):
    """Get interactions that need NLP processing."""
    if reprocess:
        query = {}
    else:
        query = {'interaccion.nlp.procesado': {'$ne': True}}

    cursor = db.drug_interactions.find(
        query,
        {
            '_id': 1,
            'medicamento_origen': 1,
            'medicamento_destino': 1,
            'interaccion.efecto': 1,
            'interaccion.recomendacion': 1
        }
    )

    if sample > 0:
        cursor = cursor.limit(sample)

    return list(cursor)


def update_interaction(db, interaction_id, nlp_result):
    """Update a single interaction with NLP results."""
    update = {'$set': nlp_result.to_mongo_update()}
    db.drug_interactions.update_one({'_id': interaction_id}, update)


def show_statistics(db, logger):
    """Show current NLP processing statistics."""
    logger.info("=" * 60)
    logger.info("NLP PROCESSING STATISTICS")
    logger.info("=" * 60)

    # Total counts
    total = db.drug_interactions.count_documents({})
    processed = db.drug_interactions.count_documents({'interaccion.nlp.procesado': True})
    unprocessed = total - processed

    logger.info(f"\nTotal interactions: {total}")
    logger.info(f"Processed: {processed} ({100*processed/total:.1f}%)")
    logger.info(f"Unprocessed: {unprocessed} ({100*unprocessed/total:.1f}%)")

    if processed == 0:
        logger.info("\nNo interactions have been processed yet.")
        return

    # Severity distribution
    logger.info("\n--- Severity Distribution ---")
    pipeline = [
        {'$match': {'interaccion.nlp.procesado': True}},
        {'$group': {'_id': '$interaccion.nlp.severidad', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    for doc in db.drug_interactions.aggregate(pipeline):
        pct = 100 * doc['count'] / processed
        logger.info(f"  {doc['_id']}: {doc['count']} ({pct:.1f}%)")

    # Type distribution
    logger.info("\n--- Interaction Type Distribution ---")
    pipeline = [
        {'$match': {'interaccion.nlp.procesado': True}},
        {'$group': {'_id': '$interaccion.nlp.tipo', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 10}
    ]
    for doc in db.drug_interactions.aggregate(pipeline):
        pct = 100 * doc['count'] / processed
        logger.info(f"  {doc['_id']}: {doc['count']} ({pct:.1f}%)")

    # Effect category distribution
    logger.info("\n--- Effect Category Distribution ---")
    pipeline = [
        {'$match': {'interaccion.nlp.procesado': True}},
        {'$group': {'_id': '$interaccion.nlp.categoria_efecto', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    for doc in db.drug_interactions.aggregate(pipeline):
        pct = 100 * doc['count'] / processed
        logger.info(f"  {doc['_id']}: {doc['count']} ({pct:.1f}%)")

    # Mechanism distribution
    logger.info("\n--- Mechanism Category Distribution ---")
    pipeline = [
        {'$match': {'interaccion.nlp.procesado': True}},
        {'$group': {'_id': '$interaccion.nlp.mecanismo', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    for doc in db.drug_interactions.aggregate(pipeline):
        pct = 100 * doc['count'] / processed
        logger.info(f"  {doc['_id']}: {doc['count']} ({pct:.1f}%)")

    # Top enzymes
    logger.info("\n--- Top CYP Enzymes Involved ---")
    pipeline = [
        {'$match': {'interaccion.nlp.procesado': True, 'interaccion.nlp.enzimas.0': {'$exists': True}}},
        {'$unwind': '$interaccion.nlp.enzimas'},
        {'$group': {'_id': '$interaccion.nlp.enzimas', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 10}
    ]
    for doc in db.drug_interactions.aggregate(pipeline):
        logger.info(f"  {doc['_id']}: {doc['count']}")

    # Average confidence
    pipeline = [
        {'$match': {'interaccion.nlp.procesado': True}},
        {'$group': {'_id': None, 'avg_confidence': {'$avg': '$interaccion.nlp.confianza'}}}
    ]
    result = list(db.drug_interactions.aggregate(pipeline))
    if result:
        logger.info(f"\nAverage confidence: {result[0]['avg_confidence']:.3f}")

    # High confidence count
    high_conf = db.drug_interactions.count_documents({
        'interaccion.nlp.procesado': True,
        'interaccion.nlp.confianza': {'$gte': 0.7}
    })
    logger.info(f"High confidence (>=0.7): {high_conf} ({100*high_conf/processed:.1f}%)")


def process_interactions(db, interactions, nlp_pipeline, batch_size, logger):
    """Process interactions with NLP pipeline."""
    total = len(interactions)
    processed = 0
    errors = 0

    logger.info(f"Processing {total} interactions...")

    start_time = time.time()
    batch_start_time = start_time

    for i, interaction in enumerate(interactions):
        try:
            # Extract text
            efecto = interaction.get('interaccion', {}).get('efecto', '')
            recomendacion = interaction.get('interaccion', {}).get('recomendacion', '')

            # Analyze
            result = nlp_pipeline.analyze(efecto, recomendacion)

            # Update database
            update_interaction(db, interaction['_id'], result)

            processed += 1

        except Exception as e:
            errors += 1
            logger.error(f"Error processing interaction {interaction['_id']}: {e}")

        # Progress logging
        if (i + 1) % batch_size == 0:
            elapsed = time.time() - batch_start_time
            rate = batch_size / elapsed if elapsed > 0 else 0
            remaining = (total - i - 1) / rate if rate > 0 else 0

            logger.info(
                f"Progress: {i + 1}/{total} ({100*(i+1)/total:.1f}%) - "
                f"Rate: {rate:.0f}/sec - "
                f"ETA: {remaining:.0f}s"
            )
            batch_start_time = time.time()

    total_time = time.time() - start_time

    return processed, errors, total_time


def main():
    """Main entry point."""
    args = parse_args()
    logger = setup_logging(args.log_level)

    logger.info("=" * 60)
    logger.info("NLP PROCESSING FOR DRUG INTERACTIONS")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # Load settings
    settings = get_settings()

    # Connect to MongoDB
    mongo = MongoDBLoader(settings.mongodb_uri, settings.mongodb_db)
    if not mongo.connect():
        logger.error("Failed to connect to MongoDB")
        sys.exit(1)

    try:
        # Show statistics only
        if args.stats:
            show_statistics(mongo.db, logger)
            return

        # Initialize NLP pipeline
        nlp_pipeline = NLPPipeline()

        # Get interactions to process
        logger.info("Fetching interactions to process...")
        interactions = get_interactions_to_process(
            mongo.db,
            args.reprocess,
            args.sample
        )

        if not interactions:
            logger.info("No interactions to process.")
            show_statistics(mongo.db, logger)
            return

        logger.info(f"Found {len(interactions)} interactions to process")

        # Process
        processed, errors, total_time = process_interactions(
            mongo.db,
            interactions,
            nlp_pipeline,
            args.batch_size,
            logger
        )

        # Summary
        logger.info("=" * 60)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Processed: {processed}")
        logger.info(f"Errors: {errors}")
        logger.info(f"Total time: {total_time:.2f} seconds")
        logger.info(f"Rate: {processed/total_time:.1f} interactions/second")

        # Show final statistics
        show_statistics(mongo.db, logger)

    finally:
        mongo.disconnect()


if __name__ == '__main__':
    main()
