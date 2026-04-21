"""
MongoDB Loader for drug interaction data.
Handles connection, collection creation, and data insertion.
"""
from typing import List, Dict, Any, Optional
import logging
from pymongo import MongoClient, ASCENDING, TEXT
from pymongo.errors import ConnectionFailure, BulkWriteError
from pymongo.database import Database
from pymongo.collection import Collection

logger = logging.getLogger(__name__)


class MongoDBLoader:
    """Loader for MongoDB database."""

    # Collection names
    COLLECTIONS = {
        'drugs': 'drugs',
        'active_ingredients': 'active_ingredients',
        'laboratories': 'laboratories',
        'atc_codes': 'atc_codes',
        'pharmaceutical_forms': 'pharmaceutical_forms',
        'simplified_pharmaceutical_forms': 'simplified_pharmaceutical_forms',
        'administration_routes': 'administration_routes',
        'excipients': 'excipients',
        'package_types': 'package_types',
        'content_units': 'content_units',
        'registration_statuses': 'registration_statuses',
        'drug_interactions': 'drug_interactions',
        'dcsa': 'dcsa',
        'dcp': 'dcp',
        'dcpf': 'dcpf'
    }

    def __init__(self, uri: str, database: str):
        """
        Initialize the MongoDB loader.

        Args:
            uri: MongoDB connection URI
            database: Database name
        """
        self.uri = uri
        self.database_name = database
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None

    def connect(self) -> bool:
        """
        Connect to MongoDB.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to MongoDB...")
            self.client = MongoClient(self.uri)

            # Verify connection
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]

            logger.info(f"Connected to MongoDB database: {self.database_name}")
            return True
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False

    def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    def setup_collections(self):
        """Create collections and indexes."""
        if self.db is None:
            raise ValueError("Not connected to database. Call connect() first.")

        logger.info("Setting up collections and indexes...")

        # Drugs collection indexes
        self._create_indexes('drugs', [
            ([('cod_nacion', ASCENDING)], {'unique': True}),
            ([('nro_definitivo', ASCENDING)], {}),
            ([('atc.codigo', ASCENDING)], {}),
            ([('laboratorio_titular.codigo', ASCENDING)], {}),
            ([('laboratorio_comercializador.codigo', ASCENDING)], {}),
            ([('situacion_registro.codigo', ASCENDING)], {}),
            ([('comercializado', ASCENDING)], {}),
            ([('clasificacion.uso_hospitalario', ASCENDING), ('comercializado', ASCENDING)], {}),
            ([('atc.codigo', ASCENDING), ('comercializado', ASCENDING)], {}),
            ([('atc.interacciones.atc_interaccion', ASCENDING)], {}),
            ([('formas_farmaceuticas.composicion.principio_activo.codigo', ASCENDING)], {}),
            ([('nombre_comercial', TEXT), ('presentacion', TEXT)], {})
        ])

        # Drug interactions collection indexes
        self._create_indexes('drug_interactions', [
            ([('medicamento_origen.cod_nacion', ASCENDING)], {}),
            ([('medicamento_origen.atc', ASCENDING)], {}),
            ([('medicamento_destino.atc', ASCENDING)], {}),
            ([('interaccion.nlp.severidad', ASCENDING)], {}),
            ([('interaccion.nlp.tipo', ASCENDING)], {}),
            ([('interaccion.efecto', TEXT), ('interaccion.recomendacion', TEXT)], {})
        ])

        # Reference collection indexes
        self._create_indexes('active_ingredients', [
            ([('codigo', ASCENDING)], {'unique': True}),
            ([('nombre', TEXT)], {})
        ])

        self._create_indexes('laboratories', [
            ([('codigo', ASCENDING)], {'unique': True}),
            ([('nombre', TEXT)], {})
        ])

        self._create_indexes('atc_codes', [
            ([('codigo', ASCENDING)], {'unique': True}),
            ([('descripcion', TEXT)], {})
        ])

        self._create_indexes('pharmaceutical_forms', [
            ([('codigo', ASCENDING)], {'unique': True})
        ])

        self._create_indexes('administration_routes', [
            ([('codigo', ASCENDING)], {'unique': True})
        ])

        self._create_indexes('excipients', [
            ([('codigo', ASCENDING)], {'unique': True})
        ])

        self._create_indexes('package_types', [
            ([('codigo', ASCENDING)], {'unique': True})
        ])

        self._create_indexes('content_units', [
            ([('codigo', ASCENDING)], {'unique': True})
        ])

        self._create_indexes('registration_statuses', [
            ([('codigo', ASCENDING)], {'unique': True})
        ])

        logger.info("Collections and indexes created successfully")

    def _create_indexes(self, collection_name: str, indexes: List):
        """Create indexes for a collection."""
        collection = self.db[collection_name]
        for index_spec, options in indexes:
            try:
                collection.create_index(index_spec, **options)
            except Exception as e:
                logger.warning(f"Could not create index on {collection_name}: {e}")

    def clear_collection(self, collection_name: str):
        """Clear all documents from a collection."""
        if self.db is None:
            raise ValueError("Not connected to database.")

        result = self.db[collection_name].delete_many({})
        logger.info(f"Cleared {result.deleted_count} documents from {collection_name}")

    def clear_all_collections(self):
        """Clear all collections."""
        for collection_name in self.COLLECTIONS.values():
            self.clear_collection(collection_name)

    def insert_many(self, collection_name: str, documents: List[Dict], batch_size: int = 1000) -> int:
        """
        Insert multiple documents into a collection.

        Args:
            collection_name: Name of the collection
            documents: List of documents to insert
            batch_size: Number of documents to insert per batch

        Returns:
            Number of documents inserted
        """
        if self.db is None:
            raise ValueError("Not connected to database.")

        if not documents:
            return 0

        collection = self.db[collection_name]
        total_inserted = 0

        # Insert in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            try:
                result = collection.insert_many(batch, ordered=False)
                total_inserted += len(result.inserted_ids)
            except BulkWriteError as e:
                # Some documents may have been inserted
                total_inserted += e.details.get('nInserted', 0)
                logger.warning(f"Bulk write error in {collection_name}: {e.details.get('writeErrors', [])[:5]}")

            if (i + batch_size) % 5000 == 0:
                logger.info(f"Inserted {total_inserted} documents into {collection_name}...")

        logger.info(f"Inserted {total_inserted} documents into {collection_name}")
        return total_inserted

    def insert_one(self, collection_name: str, document: Dict) -> bool:
        """Insert a single document."""
        if self.db is None:
            raise ValueError("Not connected to database.")

        try:
            self.db[collection_name].insert_one(document)
            return True
        except Exception as e:
            logger.error(f"Error inserting document into {collection_name}: {e}")
            return False

    def upsert_one(self, collection_name: str, filter_query: Dict, document: Dict) -> bool:
        """Upsert a single document."""
        if self.db is None:
            raise ValueError("Not connected to database.")

        try:
            self.db[collection_name].replace_one(filter_query, document, upsert=True)
            return True
        except Exception as e:
            logger.error(f"Error upserting document into {collection_name}: {e}")
            return False

    def get_collection(self, collection_name: str) -> Collection:
        """Get a collection object."""
        if self.db is None:
            raise ValueError("Not connected to database.")
        return self.db[collection_name]

    def count_documents(self, collection_name: str, filter_query: Dict = None) -> int:
        """Count documents in a collection."""
        if self.db is None:
            raise ValueError("Not connected to database.")
        return self.db[collection_name].count_documents(filter_query or {})

    def get_stats(self) -> Dict[str, int]:
        """Get document counts for all collections."""
        stats = {}
        for name in self.COLLECTIONS.values():
            stats[name] = self.count_documents(name)
        return stats
