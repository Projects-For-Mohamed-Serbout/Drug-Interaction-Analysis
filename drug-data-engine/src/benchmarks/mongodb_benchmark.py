"""
MongoDB Benchmark Queries for Performance Testing.

Implements various query types to benchmark MongoDB performance
for drug interaction data. Each query is categorized and designed
to have an equivalent counterpart in the Neo4j benchmark.
"""
from typing import List, Dict, Any, Optional
import logging
from pymongo import MongoClient
from pymongo.database import Database

from .base_benchmark import BaseBenchmark, BenchmarkResult, QueryCategory

logger = logging.getLogger(__name__)


class MongoDBBenchmark(BaseBenchmark):
    """MongoDB benchmark implementation."""

    def __init__(self, uri: str, database: str):
        super().__init__("MongoDB")
        self.uri = uri
        self.database_name_db = database
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None

    def connect(self) -> bool:
        """Connect to MongoDB."""
        try:
            self.client = MongoClient(self.uri)
            self.db = self.client[self.database_name_db]
            self.client.admin.command('ping')
            logger.info("Connected to MongoDB")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False

    def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    def warmup(self):
        """Warm up MongoDB connection with simple queries."""
        logger.info("Warming up MongoDB...")
        self.db.drugs.find_one()
        self.db.drug_interactions.find_one()
        list(self.db.drugs.find().limit(10))
        self.db.active_ingredients.find_one()
        logger.info("MongoDB warmup complete")

    def get_database_info(self) -> Dict[str, Any]:
        """Return MongoDB server information."""
        try:
            server_info = self.client.server_info()
            db_stats = self.db.command('dbStats')
            # Active storage engine (serverStatus.storageEngine.name), not the
            # list of *available* engines in buildInfo.storageEngines.
            try:
                storage_engine = self.db.command('serverStatus').get(
                    'storageEngine', {}).get('name', 'wiredTiger')
            except Exception:
                storage_engine = 'wiredTiger'  # Atlas default; serverStatus may be restricted
            return {
                'version': server_info.get('version', 'unknown'),
                'storage_engine': storage_engine,
                'database': self.database_name_db,
                'collections': len(self.db.list_collection_names()),
                'data_size_mb': round(db_stats.get('dataSize', 0) / (1024 * 1024), 2),
                'index_size_mb': round(db_stats.get('indexSize', 0) / (1024 * 1024), 2),
                'document_count': {
                    'drugs': self.db.drugs.count_documents({}),
                    'drug_interactions': self.db.drug_interactions.count_documents({}),
                    'active_ingredients': self.db.active_ingredients.count_documents({}),
                    'atc_codes': self.db.atc_codes.count_documents({}),
                }
            }
        except Exception as e:
            logger.warning(f"Could not collect MongoDB info: {e}")
            return {'version': 'unknown', 'error': str(e)}

    # =========================================================================
    # CATEGORY: Point Lookup
    # =========================================================================

    def query_drug_by_id(self, cod_nacion: str) -> Dict:
        """Q1: Find a single drug by its national code."""
        return self.db.drugs.find_one({'cod_nacion': cod_nacion})

    # =========================================================================
    # CATEGORY: Relationship Traversal
    # =========================================================================

    def query_interactions_for_drug(self, cod_nacion: str) -> List[Dict]:
        """Q2: Find all interactions where a specific drug is the source."""
        return list(self.db.drug_interactions.find(
            {'medicamento_origen.cod_nacion': cod_nacion},
            {
                'medicamento_origen.nombre': 1,
                'medicamento_destino.atc': 1,
                'medicamento_destino.nombre': 1,
                'interaccion.efecto': 1,
            }
        ))

    # =========================================================================
    # CATEGORY: Range Scan (NLP-classified fields)
    # =========================================================================

    def query_contraindicated_interactions(self) -> List[Dict]:
        """Q3: Find interactions classified as contraindicated by NLP."""
        return list(self.db.drug_interactions.find(
            {'interaccion.nlp.severidad': 'contraindicated'},
            {
                'medicamento_origen.nombre': 1,
                'medicamento_destino.nombre': 1,
                'interaccion.efecto': 1,
            }
        ).limit(1000))

    def query_cardiac_interactions(self) -> List[Dict]:
        """Q4: Find interactions classified as 'cardiac' type by NLP."""
        return list(self.db.drug_interactions.find(
            {'interaccion.nlp.tipo': 'cardiac'},
            {
                'medicamento_origen.nombre': 1,
                'medicamento_destino.nombre': 1,
                'interaccion.efecto': 1,
            }
        ).limit(1000))

    # =========================================================================
    # CATEGORY: Text Search
    # =========================================================================

    def query_drugs_by_name_pattern(self, pattern: str) -> List[Dict]:
        """Q5: Find drugs matching a name pattern (regex)."""
        return list(self.db.drugs.find(
            {'nombre_comercial': {'$regex': pattern, '$options': 'i'}},
            {'cod_nacion': 1, 'nombre_comercial': 1}
        ).limit(100))

    # =========================================================================
    # CATEGORY: Aggregation
    # =========================================================================

    def query_interaction_count_by_severity(self) -> List[Dict]:
        """Q6: Count interactions grouped by NLP severity."""
        pipeline = [
            {'$match': {'interaccion.nlp.severidad': {'$exists': True, '$ne': None}}},
            {'$group': {
                '_id': '$interaccion.nlp.severidad',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ]
        return list(self.db.drug_interactions.aggregate(pipeline))

    # =========================================================================
    # CATEGORY: Range Scan (ATC prefix)
    # =========================================================================

    def query_drugs_by_atc_prefix(self, prefix: str) -> List[Dict]:
        """Q7: Find all drugs with ATC codes starting with prefix."""
        return list(self.db.drugs.find(
            {'atc.codigo': {'$regex': f'^{prefix}'}},
            {'cod_nacion': 1, 'nombre_comercial': 1, 'atc.codigo': 1}
        ).limit(500))

    # =========================================================================
    # CATEGORY: Complex Filter
    # =========================================================================

    def query_complex_interaction_filter(self, atc_prefix: str) -> List[Dict]:
        """Q8: Complex query combining NLP severity + type + ATC class."""
        return list(self.db.drug_interactions.find({
            'interaccion.nlp.severidad': {'$in': ['contraindicated', 'severe']},
            'interaccion.nlp.tipo': 'cardiac',
            'medicamento_origen.atc': {'$regex': f'^{atc_prefix}'}
        }).limit(500))

    # =========================================================================
    # CATEGORY: Aggregation
    # =========================================================================

    def query_top_interacting_drugs(self, limit: int = 10) -> List[Dict]:
        """Q9: Find drugs with the most interactions (aggregation)."""
        pipeline = [
            {'$group': {
                '_id': '$medicamento_origen.cod_nacion',
                'nombre': {'$first': '$medicamento_origen.nombre'},
                'interaction_count': {'$sum': 1}
            }},
            {'$sort': {'interaction_count': -1}},
            {'$limit': limit}
        ]
        return list(self.db.drug_interactions.aggregate(pipeline))

    # =========================================================================
    # CATEGORY: Relationship Traversal (ingredient lookup)
    # =========================================================================

    def query_drugs_with_ingredient(self, ingredient_name: str) -> List[Dict]:
        """Q10: Find drugs containing a specific active ingredient."""
        return list(self.db.drugs.find(
            {'formas_farmaceuticas.composicion.principio_activo.nombre':
             {'$regex': ingredient_name, '$options': 'i'}},
            {'cod_nacion': 1, 'nombre_comercial': 1}
        ).limit(100))

    # =========================================================================
    # CATEGORY: Aggregation (effect categories)
    # =========================================================================

    def query_effect_category_distribution(self) -> List[Dict]:
        """Q11: Get distribution of interaction effect categories from NLP."""
        pipeline = [
            {'$match': {'interaccion.nlp.tipo': {'$exists': True, '$ne': None}}},
            {'$group': {
                '_id': '$interaccion.nlp.tipo',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ]
        return list(self.db.drug_interactions.aggregate(pipeline))

    # =========================================================================
    # CATEGORY: Complex Filter (cross-class)
    # =========================================================================

    def query_interactions_between_atc_classes(
        self, atc1_prefix: str, atc2_prefix: str
    ) -> List[Dict]:
        """Q12: Find interactions between two ATC drug classes."""
        return list(self.db.drug_interactions.find({
            'medicamento_origen.atc': {'$regex': f'^{atc1_prefix}'},
            'medicamento_destino.atc': {'$regex': f'^{atc2_prefix}'}
        }, {
            'medicamento_origen.nombre': 1,
            'medicamento_destino.nombre': 1,
            'interaccion.efecto': 1,
        }).limit(500))

    # =========================================================================
    # CATEGORY: Aggregation (mechanism distribution)
    # =========================================================================

    def query_mechanism_distribution(self) -> List[Dict]:
        """Q13: Get distribution of interaction mechanisms from NLP."""
        pipeline = [
            {'$match': {'interaccion.nlp.mecanismo': {'$exists': True, '$ne': None}}},
            {'$group': {
                '_id': '$interaccion.nlp.mecanismo',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ]
        return list(self.db.drug_interactions.aggregate(pipeline))

    # =========================================================================
    # CATEGORY: Complex Filter (high-risk polypharmacy)
    # =========================================================================

    def query_high_risk_drugs(self, min_interactions: int = 50) -> List[Dict]:
        """Q14: Find drugs with more than N severe/contraindicated interactions."""
        pipeline = [
            {'$match': {
                'interaccion.nlp.severidad': {'$in': ['contraindicated', 'severe']}
            }},
            {'$group': {
                '_id': '$medicamento_origen.cod_nacion',
                'nombre': {'$first': '$medicamento_origen.nombre'},
                'severe_count': {'$sum': 1}
            }},
            {'$match': {'severe_count': {'$gte': min_interactions}}},
            {'$sort': {'severe_count': -1}},
            {'$limit': 50}
        ]
        return list(self.db.drug_interactions.aggregate(pipeline))

    # =========================================================================
    # CATEGORY: Text Search (effect text)
    # =========================================================================

    def query_interactions_by_effect_text(self, keyword: str) -> List[Dict]:
        """Q15: Search interaction effect text for a keyword."""
        return list(self.db.drug_interactions.find(
            {'interaccion.efecto': {'$regex': keyword, '$options': 'i'}},
            {
                'medicamento_origen.nombre': 1,
                'medicamento_destino.nombre': 1,
                'interaccion.efecto': 1,
            }
        ).limit(200))

    # =========================================================================
    # Run All Benchmarks
    # =========================================================================
    def run_all_benchmarks(self, iterations: int = 10) -> List[BenchmarkResult]:
        """Run all benchmark queries."""
        self.clear_results()

        # Sample data for parameterized queries
        sample_drug_id = '600023'
        sample_pattern = 'AMOXICILINA'
        sample_atc_prefix = 'N06'
        sample_ingredient = 'PARACETAMOL'

        benchmarks = [
            # Q1: Point Lookup
            ('Q01_drug_lookup',
             'Find single drug by national code (indexed)',
             QueryCategory.POINT_LOOKUP,
             self.query_drug_by_id, sample_drug_id),

            # Q2: Relationship Traversal
            ('Q02_interactions_for_drug',
             'Find all interactions for a specific drug',
             QueryCategory.RELATIONSHIP_TRAVERSAL,
             self.query_interactions_for_drug, sample_drug_id),

            # Q3: Range Scan (NLP field)
            ('Q03_contraindicated',
             'Find interactions with NLP severity = CONTRAINDICATED',
             QueryCategory.RANGE_SCAN,
             self.query_contraindicated_interactions),

            # Q4: Range Scan (NLP field)
            ('Q04_cardiac_interactions',
             'Find interactions with NLP type = CARDIAC',
             QueryCategory.RANGE_SCAN,
             self.query_cardiac_interactions),

            # Q5: Text Search
            ('Q05_text_search',
             'Search drugs by name pattern (regex)',
             QueryCategory.TEXT_SEARCH,
             self.query_drugs_by_name_pattern, sample_pattern),

            # Q6: Aggregation
            ('Q06_count_by_severity',
             'Count interactions grouped by NLP severity',
             QueryCategory.AGGREGATION,
             self.query_interaction_count_by_severity),

            # Q7: Range Scan (ATC prefix)
            ('Q07_atc_prefix_search',
             'Find drugs by ATC code prefix',
             QueryCategory.RANGE_SCAN,
             self.query_drugs_by_atc_prefix, sample_atc_prefix),

            # Q8: Complex Filter
            ('Q08_complex_filter',
             'Severe/contraindicated cardiac interactions for ATC class N',
             QueryCategory.COMPLEX_FILTER,
             self.query_complex_interaction_filter, 'N'),

            # Q9: Aggregation
            ('Q09_top_interacting_drugs',
             'Top 10 drugs with most interactions (aggregation)',
             QueryCategory.AGGREGATION,
             self.query_top_interacting_drugs, 10),

            # Q10: Relationship Traversal
            ('Q10_drugs_with_ingredient',
             'Find drugs containing a specific active ingredient',
             QueryCategory.RELATIONSHIP_TRAVERSAL,
             self.query_drugs_with_ingredient, sample_ingredient),

            # Q11: Aggregation
            ('Q11_type_distribution',
             'Distribution of NLP interaction types (aggregation)',
             QueryCategory.AGGREGATION,
             self.query_effect_category_distribution),

            # Q12: Complex Filter
            ('Q12_cross_class_interactions',
             'Find interactions between two ATC classes (N and C)',
             QueryCategory.COMPLEX_FILTER,
             self.query_interactions_between_atc_classes, 'N', 'C'),

            # Q13: Aggregation
            ('Q13_mechanism_distribution',
             'Distribution of NLP interaction mechanisms',
             QueryCategory.AGGREGATION,
             self.query_mechanism_distribution),

            # Q14: Complex Filter + Aggregation
            ('Q14_high_risk_drugs',
             'Drugs with 50+ severe/contraindicated interactions',
             QueryCategory.COMPLEX_FILTER,
             self.query_high_risk_drugs, 50),

            # Q15: Text Search
            ('Q15_effect_text_search',
             'Search interaction effect text for keyword',
             QueryCategory.TEXT_SEARCH,
             self.query_interactions_by_effect_text, 'QT'),
        ]

        for benchmark in benchmarks:
            name, description, category, func, *args = benchmark
            self.run_benchmark(
                name, description, func, iterations,
                category=category,
                *args
            )

        return self.results
