"""
Neo4J Benchmark Queries for Performance Testing.

Implements equivalent query types to the MongoDB benchmark, plus
graph-exclusive queries that leverage Neo4j's traversal capabilities.

IMPORTANT: In the graph model, interactions are modeled as:
    (Drug)-[:INTERACTS_WITH_ATC]->(ATCCode)
with properties: efecto, recomendacion, medicamento_nombre,
and NLP fields (severidad, tipo, mecanismo) after sync.
"""
from typing import List, Dict, Any, Optional
import logging
from neo4j import GraphDatabase, Driver

from .base_benchmark import BaseBenchmark, BenchmarkResult, QueryCategory

logger = logging.getLogger(__name__)


class Neo4JBenchmark(BaseBenchmark):
    """Neo4J benchmark implementation."""

    def __init__(self, uri: str, user: str, password: str):
        super().__init__("Neo4J")
        self.uri = uri
        self.user = user
        self.password = password
        self.driver: Optional[Driver] = None

    def connect(self) -> bool:
        """Connect to Neo4J."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            self.driver.verify_connectivity()
            logger.info("Connected to Neo4J")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4J: {e}")
            return False

    def disconnect(self):
        """Disconnect from Neo4J."""
        if self.driver:
            self.driver.close()
            logger.info("Disconnected from Neo4J")

    def warmup(self):
        """Warm up Neo4J connection with simple queries."""
        logger.info("Warming up Neo4J...")
        with self.driver.session() as session:
            session.run("MATCH (d:Drug) RETURN d LIMIT 1").single()
            session.run(
                "MATCH (d:Drug)-[i:INTERACTS_WITH_ATC]->(a:ATCCode) "
                "RETURN d, i, a LIMIT 1"
            ).single()
            list(session.run("MATCH (d:Drug) RETURN d LIMIT 10"))
            session.run("MATCH (a:ActiveIngredient) RETURN a LIMIT 1").single()
        logger.info("Neo4J warmup complete")

    def get_database_info(self) -> Dict[str, Any]:
        """Return Neo4j server information."""
        try:
            with self.driver.session() as session:
                # Server version
                result = session.run(
                    "CALL dbms.components() YIELD name, versions "
                    "RETURN name, versions[0] AS version"
                )
                record = result.single()
                version = record['version'] if record else 'unknown'

                # Node and relationship counts
                counts = {}
                for label in ['Drug', 'ActiveIngredient', 'Laboratory',
                              'ATCCode', 'PharmaceuticalForm']:
                    r = session.run(
                        f"MATCH (n:{label}) RETURN count(n) AS c"
                    ).single()
                    counts[label] = r['c'] if r else 0

                r = session.run(
                    "MATCH ()-[i:INTERACTS_WITH_ATC]->() RETURN count(i) AS c"
                ).single()
                counts['INTERACTS_WITH_ATC'] = r['c'] if r else 0

                # Check NLP coverage
                r = session.run(
                    "MATCH ()-[i:INTERACTS_WITH_ATC]->() "
                    "WHERE i.severidad IS NOT NULL "
                    "RETURN count(i) AS c"
                ).single()
                counts['with_nlp_data'] = r['c'] if r else 0

                return {
                    'version': version,
                    'database': 'neo4j',
                    'node_counts': counts,
                    'nlp_coverage': (
                        round(counts['with_nlp_data'] / counts['INTERACTS_WITH_ATC'] * 100, 1)
                        if counts['INTERACTS_WITH_ATC'] > 0 else 0
                    ),
                }
        except Exception as e:
            logger.warning(f"Could not collect Neo4j info: {e}")
            return {'version': 'unknown', 'error': str(e)}

    def _run_query(self, query: str, parameters: dict = None) -> List[Dict]:
        """Run a Cypher query and return results as list of dicts."""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]

    # =====================================================================
    # Q1: Point Lookup — Find drug by ID
    # =====================================================================
    def query_drug_by_id(self, cod_nacion: str) -> Dict:
        """Find a single drug by its national code."""
        query = """
        MATCH (d:Drug {cod_nacion: $cod_nacion})
        RETURN d
        """
        results = self._run_query(query, {'cod_nacion': cod_nacion})
        return results[0] if results else None

    # =====================================================================
    # Q2: Relationship Traversal — Interactions for a drug
    #     Drug -> INTERACTS_WITH_ATC -> ATCCode (correct pattern)
    # =====================================================================
    def query_interactions_for_drug(self, cod_nacion: str) -> List[Dict]:
        """Find all interactions where a specific drug is the source."""
        query = """
        MATCH (d:Drug {cod_nacion: $cod_nacion})-[i:INTERACTS_WITH_ATC]->(a:ATCCode)
        RETURN d.nombre_comercial AS source_drug,
               a.codigo AS target_atc,
               i.medicamento_nombre AS target_drug_name,
               i.efecto AS effect
        """
        return self._run_query(query, {'cod_nacion': cod_nacion})

    # =====================================================================
    # Q3: Range Scan — Contraindicated interactions (NLP severity)
    # =====================================================================
    def query_contraindicated_interactions(self) -> List[Dict]:
        """Find interactions classified as CONTRAINDICATED by NLP."""
        query = """
        MATCH (d:Drug)-[i:INTERACTS_WITH_ATC]->(a:ATCCode)
        WHERE i.severidad = 'contraindicated'
        RETURN d.nombre_comercial AS source_drug,
               a.codigo AS target_atc,
               i.medicamento_nombre AS target_drug_name,
               i.efecto AS effect
        LIMIT 1000
        """
        return self._run_query(query)

    # =====================================================================
    # Q4: Range Scan — Cardiac interactions (NLP type)
    # =====================================================================
    def query_cardiac_interactions(self) -> List[Dict]:
        """Find interactions classified as CARDIAC type by NLP."""
        query = """
        MATCH (d:Drug)-[i:INTERACTS_WITH_ATC]->(a:ATCCode)
        WHERE i.tipo = 'cardiac'
        RETURN d.nombre_comercial AS source_drug,
               a.codigo AS target_atc,
               i.medicamento_nombre AS target_drug_name,
               i.efecto AS effect
        LIMIT 1000
        """
        return self._run_query(query)

    # =====================================================================
    # Q5: Text Search — Drugs by name pattern
    # =====================================================================
    def query_drugs_by_name_pattern(self, pattern: str) -> List[Dict]:
        """Find drugs matching a name pattern."""
        query = """
        MATCH (d:Drug)
        WHERE d.nombre_comercial CONTAINS $pattern
        RETURN d.cod_nacion AS cod_nacion,
               d.nombre_comercial AS nombre_comercial
        LIMIT 100
        """
        return self._run_query(query, {'pattern': pattern})

    # =====================================================================
    # Q6: Aggregation — Count interactions by NLP severity
    # =====================================================================
    def query_interaction_count_by_severity(self) -> List[Dict]:
        """Count interactions grouped by NLP severity."""
        query = """
        MATCH ()-[i:INTERACTS_WITH_ATC]->()
        WHERE i.severidad IS NOT NULL
        RETURN i.severidad AS _id, count(*) AS count
        ORDER BY count DESC
        """
        return self._run_query(query)

    # =====================================================================
    # Q7: Range Scan — Drugs by ATC code prefix
    # =====================================================================
    def query_drugs_by_atc_prefix(self, prefix: str) -> List[Dict]:
        """Find all drugs with ATC codes starting with prefix."""
        query = """
        MATCH (d:Drug)-[:CLASSIFIED_AS]->(a:ATCCode)
        WHERE a.codigo STARTS WITH $prefix
        RETURN DISTINCT d.cod_nacion AS cod_nacion,
               d.nombre_comercial AS nombre_comercial,
               a.codigo AS atc_codigo
        LIMIT 500
        """
        return self._run_query(query, {'prefix': prefix})

    # =====================================================================
    # Q8: Complex Filter — Severe cardiac interactions for ATC class
    # =====================================================================
    def query_complex_interaction_filter(self, atc_prefix: str) -> List[Dict]:
        """Complex query: severe/contraindicated + cardiac + ATC class."""
        query = """
        MATCH (d:Drug)-[i:INTERACTS_WITH_ATC]->(a:ATCCode)
        MATCH (d)-[:CLASSIFIED_AS]->(drug_atc:ATCCode)
        WHERE drug_atc.codigo STARTS WITH $atc_prefix
          AND i.severidad IN ['contraindicated', 'severe']
          AND i.tipo = 'cardiac'
        RETURN d.nombre_comercial AS source_drug,
               a.codigo AS target_atc,
               drug_atc.codigo AS drug_atc_code,
               i.efecto AS effect
        LIMIT 500
        """
        return self._run_query(query, {'atc_prefix': atc_prefix})

    # =====================================================================
    # Q9: Aggregation — Top drugs with most interactions
    # =====================================================================
    def query_top_interacting_drugs(self, limit: int = 10) -> List[Dict]:
        """Find drugs with the most interactions."""
        query = """
        MATCH (d:Drug)-[i:INTERACTS_WITH_ATC]->()
        RETURN d.cod_nacion AS cod_nacion,
               d.nombre_comercial AS nombre,
               count(i) AS interaction_count
        ORDER BY interaction_count DESC
        LIMIT $limit
        """
        return self._run_query(query, {'limit': limit})

    # =====================================================================
    # Q10: Relationship Traversal — Drugs with ingredient
    # =====================================================================
    def query_drugs_with_ingredient(self, ingredient_name: str) -> List[Dict]:
        """Find drugs containing a specific active ingredient."""
        query = """
        MATCH (d:Drug)-[:CONTAINS]->(ing:ActiveIngredient)
        WHERE ing.nombre CONTAINS $ingredient_name
        RETURN DISTINCT d.cod_nacion AS cod_nacion,
               d.nombre_comercial AS nombre_comercial
        LIMIT 100
        """
        return self._run_query(query, {'ingredient_name': ingredient_name})

    # =====================================================================
    # Q11: Aggregation — Distribution of NLP interaction types
    # =====================================================================
    def query_effect_category_distribution(self) -> List[Dict]:
        """Get distribution of NLP interaction types."""
        query = """
        MATCH ()-[i:INTERACTS_WITH_ATC]->()
        WHERE i.tipo IS NOT NULL
        RETURN i.tipo AS _id, count(*) AS count
        ORDER BY count DESC
        """
        return self._run_query(query)

    # =====================================================================
    # Q12: Complex Filter — Interactions between two ATC classes
    # =====================================================================
    def query_interactions_between_atc_classes(
        self, atc1_prefix: str, atc2_prefix: str
    ) -> List[Dict]:
        """Find interactions between two ATC drug classes."""
        query = """
        MATCH (d:Drug)-[:CLASSIFIED_AS]->(a1:ATCCode)
        WHERE a1.codigo STARTS WITH $atc1_prefix
        MATCH (d)-[i:INTERACTS_WITH_ATC]->(a2:ATCCode)
        WHERE a2.codigo STARTS WITH $atc2_prefix
        RETURN d.nombre_comercial AS source_drug,
               a1.codigo AS source_atc,
               a2.codigo AS target_atc,
               i.efecto AS effect
        LIMIT 500
        """
        return self._run_query(query, {
            'atc1_prefix': atc1_prefix,
            'atc2_prefix': atc2_prefix
        })

    # =====================================================================
    # Q13: Aggregation — Distribution of NLP mechanisms
    # =====================================================================
    def query_mechanism_distribution(self) -> List[Dict]:
        """Get distribution of NLP interaction mechanisms."""
        query = """
        MATCH ()-[i:INTERACTS_WITH_ATC]->()
        WHERE i.mecanismo IS NOT NULL
        RETURN i.mecanismo AS _id, count(*) AS count
        ORDER BY count DESC
        """
        return self._run_query(query)

    # =====================================================================
    # Q14: Complex Filter — High-risk drugs (aggregation + filter)
    # =====================================================================
    def query_high_risk_drugs(self, min_interactions: int = 50) -> List[Dict]:
        """Find drugs with 50+ severe/contraindicated interactions."""
        query = """
        MATCH (d:Drug)-[i:INTERACTS_WITH_ATC]->()
        WHERE i.severidad IN ['contraindicated', 'severe']
        WITH d, count(i) AS severe_count
        WHERE severe_count >= $min_interactions
        RETURN d.cod_nacion AS cod_nacion,
               d.nombre_comercial AS nombre,
               severe_count
        ORDER BY severe_count DESC
        LIMIT 50
        """
        return self._run_query(query, {'min_interactions': min_interactions})

    # =====================================================================
    # Q15: Text Search — Effect text keyword search
    # =====================================================================
    def query_interactions_by_effect_text(self, keyword: str) -> List[Dict]:
        """Search interaction effect text for a keyword."""
        query = """
        MATCH (d:Drug)-[i:INTERACTS_WITH_ATC]->(a:ATCCode)
        WHERE i.efecto CONTAINS $keyword
        RETURN d.nombre_comercial AS source_drug,
               a.codigo AS target_atc,
               i.efecto AS effect
        LIMIT 200
        """
        return self._run_query(query, {'keyword': keyword})

    # =====================================================================
    # GRAPH-EXCLUSIVE QUERIES (Q16-Q19)
    # These queries showcase Neo4j's native graph traversal strengths
    # and have no direct MongoDB equivalent.
    # =====================================================================

    def query_interaction_chain(self, cod_nacion: str, hops: int = 2) -> List[Dict]:
        """
        Q16: Find indirect interaction chains through ATC codes.
        Drug1 -[INTERACTS_WITH_ATC]-> ATC1 <-[CLASSIFIED_AS]- Drug2
              -[INTERACTS_WITH_ATC]-> ATC2
        Shows drugs that interact with the same drug class as the source.
        """
        query = """
        MATCH (start:Drug {cod_nacion: $cod_nacion})-[i1:INTERACTS_WITH_ATC]->(a1:ATCCode)
              <-[:CLASSIFIED_AS]-(d2:Drug)-[i2:INTERACTS_WITH_ATC]->(a2:ATCCode)
        WHERE start <> d2
        RETURN start.nombre_comercial AS source_drug,
               a1.codigo AS shared_atc,
               d2.nombre_comercial AS intermediate_drug,
               a2.codigo AS secondary_atc,
               i1.efecto AS first_effect,
               i2.efecto AS second_effect
        LIMIT 100
        """
        return self._run_query(query, {'cod_nacion': cod_nacion})

    def query_common_interaction_targets(
        self, cod_nacion1: str, cod_nacion2: str
    ) -> List[Dict]:
        """
        Q17: Find ATC codes that both drugs interact with.
        Shows shared pharmacological targets between two drugs.
        """
        query = """
        MATCH (d1:Drug {cod_nacion: $cod1})-[i1:INTERACTS_WITH_ATC]->(a:ATCCode)
              <-[i2:INTERACTS_WITH_ATC]-(d2:Drug {cod_nacion: $cod2})
        RETURN a.codigo AS shared_atc_code,
               a.descripcion AS atc_description,
               i1.efecto AS drug1_effect,
               i2.efecto AS drug2_effect
        """
        return self._run_query(query, {'cod1': cod_nacion1, 'cod2': cod_nacion2})

    def query_drugs_in_same_class_with_interactions(
        self, atc_prefix: str
    ) -> List[Dict]:
        """
        Q18: Find drugs in the same ATC class and their mutual interactions.
        Demonstrates graph pattern matching for therapeutic alternatives analysis.
        """
        query = """
        MATCH (d1:Drug)-[:CLASSIFIED_AS]->(a:ATCCode)
        WHERE a.codigo STARTS WITH $prefix
        MATCH (d1)-[i:INTERACTS_WITH_ATC]->(target:ATCCode)
        RETURN d1.nombre_comercial AS drug_name,
               a.codigo AS drug_atc,
               count(i) AS interaction_count
        ORDER BY interaction_count DESC
        LIMIT 50
        """
        return self._run_query(query, {'prefix': atc_prefix})

    def query_atc_interaction_network(self) -> List[Dict]:
        """
        Q19: Build the ATC-level interaction network.
        Aggregates drug-level interactions to ATC class level,
        showing which drug classes interact most frequently.
        """
        query = """
        MATCH (d:Drug)-[:CLASSIFIED_AS]->(source_atc:ATCCode)
        MATCH (d)-[i:INTERACTS_WITH_ATC]->(target_atc:ATCCode)
        WHERE size(source_atc.codigo) >= 3
          AND size(target_atc.codigo) >= 3
        RETURN source_atc.codigo AS source_class,
               target_atc.codigo AS target_class,
               count(i) AS interaction_count
        ORDER BY interaction_count DESC
        LIMIT 50
        """
        return self._run_query(query)

    # =====================================================================
    # Run All Benchmarks
    # =====================================================================
    def run_all_benchmarks(self, iterations: int = 10) -> List[BenchmarkResult]:
        """Run all benchmark queries."""
        self.clear_results()

        # Sample data for parameterized queries
        sample_drug_id = '600023'
        sample_drug_id_2 = '600024'
        sample_pattern = 'AMOXICILINA'
        sample_atc_prefix = 'N06'
        sample_ingredient = 'PARACETAMOL'

        benchmarks = [
            # --- Comparable queries (Q01-Q15, same as MongoDB) ---

            ('Q01_drug_lookup',
             'Find single drug by national code (indexed)',
             QueryCategory.POINT_LOOKUP,
             self.query_drug_by_id, sample_drug_id),

            ('Q02_interactions_for_drug',
             'Find all interactions for a specific drug',
             QueryCategory.RELATIONSHIP_TRAVERSAL,
             self.query_interactions_for_drug, sample_drug_id),

            ('Q03_contraindicated',
             'Find interactions with NLP severity = CONTRAINDICATED',
             QueryCategory.RANGE_SCAN,
             self.query_contraindicated_interactions),

            ('Q04_cardiac_interactions',
             'Find interactions with NLP type = CARDIAC',
             QueryCategory.RANGE_SCAN,
             self.query_cardiac_interactions),

            ('Q05_text_search',
             'Search drugs by name pattern (CONTAINS)',
             QueryCategory.TEXT_SEARCH,
             self.query_drugs_by_name_pattern, sample_pattern),

            ('Q06_count_by_severity',
             'Count interactions grouped by NLP severity',
             QueryCategory.AGGREGATION,
             self.query_interaction_count_by_severity),

            ('Q07_atc_prefix_search',
             'Find drugs by ATC code prefix',
             QueryCategory.RANGE_SCAN,
             self.query_drugs_by_atc_prefix, sample_atc_prefix),

            ('Q08_complex_filter',
             'Severe/contraindicated cardiac interactions for ATC class N',
             QueryCategory.COMPLEX_FILTER,
             self.query_complex_interaction_filter, 'N'),

            ('Q09_top_interacting_drugs',
             'Top 10 drugs with most interactions (aggregation)',
             QueryCategory.AGGREGATION,
             self.query_top_interacting_drugs, 10),

            ('Q10_drugs_with_ingredient',
             'Find drugs containing a specific active ingredient',
             QueryCategory.RELATIONSHIP_TRAVERSAL,
             self.query_drugs_with_ingredient, sample_ingredient),

            ('Q11_type_distribution',
             'Distribution of NLP interaction types (aggregation)',
             QueryCategory.AGGREGATION,
             self.query_effect_category_distribution),

            ('Q12_cross_class_interactions',
             'Find interactions between two ATC classes (N and C)',
             QueryCategory.COMPLEX_FILTER,
             self.query_interactions_between_atc_classes, 'N', 'C'),

            ('Q13_mechanism_distribution',
             'Distribution of NLP interaction mechanisms',
             QueryCategory.AGGREGATION,
             self.query_mechanism_distribution),

            ('Q14_high_risk_drugs',
             'Drugs with 50+ severe/contraindicated interactions',
             QueryCategory.COMPLEX_FILTER,
             self.query_high_risk_drugs, 50),

            ('Q15_effect_text_search',
             'Search interaction effect text for keyword',
             QueryCategory.TEXT_SEARCH,
             self.query_interactions_by_effect_text, 'QT'),

            # --- Graph-exclusive queries (Q16-Q19) ---

            ('Q16_interaction_chain',
             'Indirect interaction chains through shared ATC classes',
             QueryCategory.MULTI_HOP_TRAVERSAL,
             self.query_interaction_chain, sample_drug_id, 2),

            ('Q17_common_targets',
             'Shared ATC interaction targets between two drugs',
             QueryCategory.PATTERN_MATCHING,
             self.query_common_interaction_targets,
             sample_drug_id, sample_drug_id_2),

            ('Q18_class_interaction_profile',
             'Drugs in same ATC class with their interaction counts',
             QueryCategory.PATTERN_MATCHING,
             self.query_drugs_in_same_class_with_interactions, 'N05'),

            ('Q19_atc_interaction_network',
             'ATC-level interaction network (class-to-class aggregation)',
             QueryCategory.AGGREGATION,
             self.query_atc_interaction_network),
        ]

        for benchmark in benchmarks:
            name, description, category, func, *args = benchmark
            self.run_benchmark(
                name, description, func, iterations,
                category=category,
                *args
            )

        return self.results
