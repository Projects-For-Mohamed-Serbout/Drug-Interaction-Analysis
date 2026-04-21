"""
Create Database Indexes for Performance Optimization.

This script creates indexes on frequently queried fields in both
MongoDB and Neo4J databases to improve query performance.

Usage:
    python create_indexes.py
    python create_indexes.py --mongodb-only
    python create_indexes.py --neo4j-only
    python create_indexes.py --drop-existing
"""
import argparse
import logging
from pymongo import MongoClient, ASCENDING, TEXT
from neo4j import GraphDatabase

from src.config import get_settings
from src.utils import setup_logging


logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Create database indexes for performance optimization'
    )
    parser.add_argument(
        '--mongodb-only',
        action='store_true',
        help='Create only MongoDB indexes'
    )
    parser.add_argument(
        '--neo4j-only',
        action='store_true',
        help='Create only Neo4J indexes'
    )
    parser.add_argument(
        '--drop-existing',
        action='store_true',
        help='Drop existing indexes before creating new ones'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    return parser.parse_args()


def create_mongodb_indexes(client: MongoClient, db_name: str, drop_existing: bool = False):
    """Create indexes for MongoDB collections."""
    logger.info("=" * 60)
    logger.info("CREATING MONGODB INDEXES")
    logger.info("=" * 60)

    db = client[db_name]

    # === DRUGS COLLECTION ===
    logger.info("Creating indexes for 'drugs' collection...")
    drugs_collection = db['drugs']

    if drop_existing:
        logger.info("Dropping existing indexes...")
        drugs_collection.drop_indexes()

    # Index for drug lookup by cod_nacion (primary key - probably already exists)
    drugs_collection.create_index([('cod_nacion', ASCENDING)], unique=True, name='idx_cod_nacion')
    logger.info("  ✓ Created index: cod_nacion")

    # Text index for drug name search
    drugs_collection.create_index([('nombre_comercial', TEXT)], name='idx_nombre_comercial_text')
    logger.info("  ✓ Created text index: nombre_comercial")

    # Index for active ingredient search
    drugs_collection.create_index([('principios_activos.nombre', ASCENDING)], name='idx_principios_activos')
    logger.info("  ✓ Created index: principios_activos.nombre")

    # Index for ATC code prefix search
    drugs_collection.create_index([('atc_codes', ASCENDING)], name='idx_atc_codes')
    logger.info("  ✓ Created index: atc_codes")

    # Index for pharmaceutical form filtering
    drugs_collection.create_index([('formas_farmaceuticas.nombre', ASCENDING)], name='idx_formas_farmaceuticas')
    logger.info("  ✓ Created index: formas_farmaceuticas.nombre")

    # Index for active status filtering
    drugs_collection.create_index([('estado', ASCENDING)], name='idx_estado')
    logger.info("  ✓ Created index: estado")

    # === DRUG_INTERACTIONS COLLECTION ===
    logger.info("")
    logger.info("Creating indexes for 'drug_interactions' collection...")
    interactions_collection = db['drug_interactions']

    if drop_existing:
        logger.info("Dropping existing indexes...")
        interactions_collection.drop_indexes()

    # Index for finding interactions by source drug
    interactions_collection.create_index([('cod_nacion_origen', ASCENDING)], name='idx_cod_nacion_origen')
    logger.info("  ✓ Created index: cod_nacion_origen")

    # Index for finding interactions by target drug
    interactions_collection.create_index([('cod_nacion_destino', ASCENDING)], name='idx_cod_nacion_destino')
    logger.info("  ✓ Created index: cod_nacion_destino")

    # Compound index for bidirectional lookup
    interactions_collection.create_index(
        [('cod_nacion_origen', ASCENDING), ('cod_nacion_destino', ASCENDING)],
        name='idx_interaction_pair'
    )
    logger.info("  ✓ Created compound index: cod_nacion_origen + cod_nacion_destino")

    # Index for NLP severity filtering
    interactions_collection.create_index([('nlp.severidad', ASCENDING)], name='idx_nlp_severidad')
    logger.info("  ✓ Created index: nlp.severidad")

    # Index for NLP type filtering
    interactions_collection.create_index([('nlp.tipo', ASCENDING)], name='idx_nlp_tipo')
    logger.info("  ✓ Created index: nlp.tipo")

    # Index for NLP mechanism filtering
    interactions_collection.create_index([('nlp.mecanismo', ASCENDING)], name='idx_nlp_mecanismo')
    logger.info("  ✓ Created index: nlp.mecanismo")

    # Compound index for severity + source drug (common UI query)
    interactions_collection.create_index(
        [('cod_nacion_origen', ASCENDING), ('nlp.severidad', ASCENDING)],
        name='idx_origen_severidad'
    )
    logger.info("  ✓ Created compound index: cod_nacion_origen + nlp.severidad")

    # Text index for effect/recommendation search
    interactions_collection.create_index([('efecto', TEXT), ('recomendacion', TEXT)], name='idx_efecto_recomendacion_text')
    logger.info("  ✓ Created text index: efecto + recomendacion")

    # === ACTIVE_INGREDIENTS COLLECTION ===
    logger.info("")
    logger.info("Creating indexes for 'active_ingredients' collection...")
    ingredients_collection = db['active_ingredients']

    if drop_existing:
        logger.info("Dropping existing indexes...")
        ingredients_collection.drop_indexes()

    # Text index for ingredient name search
    ingredients_collection.create_index([('nombre', TEXT)], name='idx_nombre_text')
    logger.info("  ✓ Created text index: nombre")

    # Index for code lookup
    ingredients_collection.create_index([('codigo', ASCENDING)], name='idx_codigo')
    logger.info("  ✓ Created index: codigo")

    logger.info("")
    logger.info("MongoDB indexes created successfully!")


def create_neo4j_indexes(driver, drop_existing: bool = False):
    """Create indexes for Neo4J nodes and relationships."""
    logger.info("=" * 60)
    logger.info("CREATING NEO4J INDEXES")
    logger.info("=" * 60)

    with driver.session() as session:
        if drop_existing:
            logger.info("Dropping existing indexes and constraints...")
            # Get all indexes
            result = session.run("SHOW INDEXES")
            for record in result:
                index_name = record.get('name')
                if index_name:
                    try:
                        session.run(f"DROP INDEX {index_name} IF EXISTS")
                        logger.info(f"  ✗ Dropped index: {index_name}")
                    except Exception as e:
                        logger.warning(f"  Could not drop {index_name}: {e}")

        logger.info("")
        logger.info("Creating node property indexes...")

        # === DRUG NODE INDEXES ===
        # Index for drug lookup by cod_nacion
        session.run("""
        CREATE INDEX idx_drug_cod_nacion IF NOT EXISTS
        FOR (d:Drug) ON (d.cod_nacion)
        """)
        logger.info("  ✓ Created index: Drug.cod_nacion")

        # Index for drug name search
        session.run("""
        CREATE INDEX idx_drug_nombre IF NOT EXISTS
        FOR (d:Drug) ON (d.nombre_comercial)
        """)
        logger.info("  ✓ Created index: Drug.nombre_comercial")

        # Full-text index for drug name search
        session.run("""
        CREATE FULLTEXT INDEX idx_drug_nombre_fulltext IF NOT EXISTS
        FOR (d:Drug) ON EACH [d.nombre_comercial]
        """)
        logger.info("  ✓ Created fulltext index: Drug.nombre_comercial")

        # === ATC CODE NODE INDEXES ===
        # Index for ATC code lookup
        session.run("""
        CREATE INDEX idx_atc_codigo IF NOT EXISTS
        FOR (a:ATCCode) ON (a.codigo)
        """)
        logger.info("  ✓ Created index: ATCCode.codigo")

        # === ACTIVE INGREDIENT NODE INDEXES ===
        # Index for ingredient name search
        session.run("""
        CREATE INDEX idx_ingredient_nombre IF NOT EXISTS
        FOR (i:ActiveIngredient) ON (i.nombre)
        """)
        logger.info("  ✓ Created index: ActiveIngredient.nombre")

        # Full-text index for ingredient search
        session.run("""
        CREATE FULLTEXT INDEX idx_ingredient_nombre_fulltext IF NOT EXISTS
        FOR (i:ActiveIngredient) ON EACH [i.nombre]
        """)
        logger.info("  ✓ Created fulltext index: ActiveIngredient.nombre")

        # === RELATIONSHIP PROPERTY INDEXES (Neo4J 5.0+) ===
        logger.info("")
        logger.info("Creating relationship property indexes...")

        # Index for interaction severity filtering
        try:
            session.run("""
            CREATE INDEX idx_interaction_severidad IF NOT EXISTS
            FOR ()-[i:INTERACTS_WITH_ATC]-() ON (i.severidad)
            """)
            logger.info("  ✓ Created index: INTERACTS_WITH_ATC.severidad")
        except Exception as e:
            logger.warning(f"  Could not create severity index (may require Neo4J 5.0+): {e}")

        # Index for interaction type filtering
        try:
            session.run("""
            CREATE INDEX idx_interaction_tipo IF NOT EXISTS
            FOR ()-[i:INTERACTS_WITH_ATC]-() ON (i.tipo)
            """)
            logger.info("  ✓ Created index: INTERACTS_WITH_ATC.tipo")
        except Exception as e:
            logger.warning(f"  Could not create tipo index (may require Neo4J 5.0+): {e}")

        # Index for interaction mechanism filtering
        try:
            session.run("""
            CREATE INDEX idx_interaction_mecanismo IF NOT EXISTS
            FOR ()-[i:INTERACTS_WITH_ATC]-() ON (i.mecanismo)
            """)
            logger.info("  ✓ Created index: INTERACTS_WITH_ATC.mecanismo")
        except Exception as e:
            logger.warning(f"  Could not create mecanismo index (may require Neo4J 5.0+): {e}")

        logger.info("")
        logger.info("Neo4J indexes created successfully!")


def verify_mongodb_indexes(client: MongoClient, db_name: str):
    """Verify MongoDB indexes."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("VERIFYING MONGODB INDEXES")
    logger.info("=" * 60)

    db = client[db_name]

    for collection_name in ['drugs', 'drug_interactions', 'active_ingredients']:
        collection = db[collection_name]
        indexes = list(collection.list_indexes())

        logger.info(f"\n{collection_name} collection ({len(indexes)} indexes):")
        for idx in indexes:
            logger.info(f"  - {idx['name']}: {idx.get('key', {})}")


def verify_neo4j_indexes(driver):
    """Verify Neo4J indexes."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("VERIFYING NEO4J INDEXES")
    logger.info("=" * 60)

    with driver.session() as session:
        result = session.run("SHOW INDEXES")

        logger.info("")
        for record in result:
            index_name = record.get('name', 'unknown')
            index_type = record.get('type', 'unknown')
            state = record.get('state', 'unknown')
            entity_type = record.get('entityType', 'unknown')
            properties = record.get('properties', [])

            logger.info(f"  - {index_name}")
            logger.info(f"    Type: {index_type}, State: {state}, Entity: {entity_type}")
            logger.info(f"    Properties: {properties}")


def main():
    """Main entry point."""
    args = parse_args()
    logger = setup_logging(args.log_level)

    logger.info("=" * 60)
    logger.info("DATABASE INDEX CREATION")
    logger.info("=" * 60)

    # Load settings
    settings = get_settings()

    mongo_client = None
    neo4j_driver = None

    try:
        # Create MongoDB indexes
        if not args.neo4j_only:
            logger.info("Connecting to MongoDB...")
            mongo_client = MongoClient(settings.mongodb_uri)
            mongo_client.admin.command('ping')
            logger.info("Connected to MongoDB")

            create_mongodb_indexes(mongo_client, settings.mongodb_db, args.drop_existing)
            verify_mongodb_indexes(mongo_client, settings.mongodb_db)

        # Create Neo4J indexes
        if not args.mongodb_only:
            logger.info("")
            logger.info("Connecting to Neo4J...")
            neo4j_driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            neo4j_driver.verify_connectivity()
            logger.info("Connected to Neo4J")

            create_neo4j_indexes(neo4j_driver, args.drop_existing)
            verify_neo4j_indexes(neo4j_driver)

        logger.info("")
        logger.info("=" * 60)
        logger.info("INDEX CREATION COMPLETE")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error creating indexes: {e}", exc_info=True)
        raise
    finally:
        if mongo_client:
            mongo_client.close()
        if neo4j_driver:
            neo4j_driver.close()


if __name__ == '__main__':
    main()
