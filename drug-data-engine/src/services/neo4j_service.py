"""
Neo4j Service Layer.

Provides reusable query methods for graph-based drug interaction queries.
"""
from typing import List, Dict, Optional
import logging
from neo4j import GraphDatabase, Driver

logger = logging.getLogger(__name__)


class Neo4jService:
    """Service for querying Neo4j drug interaction graph."""

    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver: Optional[Driver] = None

    def connect(self) -> bool:
        try:
            self.driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            self.driver.verify_connectivity()
            logger.info("Neo4jService connected")
            return True
        except Exception as e:
            logger.error(f"Neo4jService connection failed: {e}")
            return False

    def disconnect(self):
        if self.driver:
            self.driver.close()

    def _run_query(self, query: str, parameters: dict = None) -> List[Dict]:
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]

    # =========================================================================
    # Graph Stats
    # =========================================================================
    def get_graph_stats(self) -> Dict:
        """Get node and relationship counts."""
        node_labels = ['Drug', 'ActiveIngredient', 'Laboratory', 'ATCCode',
                       'PharmaceuticalForm', 'AdministrationRoute', 'Excipient',
                       'PackageType', 'Biomarker']
        stats = {'nodes': {}, 'relationships': {}}

        for label in node_labels:
            results = self._run_query(f"MATCH (n:{label}) RETURN count(n) as count")
            stats['nodes'][label] = results[0]['count'] if results else 0

        rel_types = ['MANUFACTURED_BY', 'MARKETED_BY', 'CONTAINS', 'CLASSIFIED_AS',
                     'HAS_FORM', 'ADMINISTERED_VIA', 'PACKAGED_IN',
                     'CONTAINS_EXCIPIENT', 'HAS_BIOMARKER',
                     'INTERACTS_WITH_ATC', 'PARENT_OF']
        for rel in rel_types:
            results = self._run_query(f"MATCH ()-[r:{rel}]->() RETURN count(r) as count")
            stats['relationships'][rel] = results[0]['count'] if results else 0

        return stats

    # =========================================================================
    # Drug Interactions (Graph Queries)
    # =========================================================================
    def get_interactions_for_drug(self, cod_nacion: str) -> List[Dict]:
        """Get all interactions for a drug using graph traversal."""
        query = """
        MATCH (d:Drug {cod_nacion: $cod_nacion})-[i:INTERACTS_WITH_ATC]->(atc:ATCCode)
        RETURN d.nombre_comercial AS source_drug,
               atc.codigo AS target_atc,
               atc.descripcion AS target_description,
               i.efecto AS effect,
               i.severidad AS severity,
               i.tipo AS type
        """
        return self._run_query(query, {'cod_nacion': cod_nacion})

    def get_interaction_chain(self, cod_nacion: str, hops: int = 2) -> List[Dict]:
        """Find multi-hop interaction chains."""
        query = f"""
        MATCH path = (start:Drug {{cod_nacion: $cod_nacion}})-[:INTERACTS_WITH_ATC*1..{hops}]->(end)
        WHERE start <> end
        RETURN [node in nodes(path) |
            CASE WHEN node:Drug THEN node.nombre_comercial
                 ELSE node.codigo END] AS chain,
               length(path) AS chain_length
        LIMIT 100
        """
        return self._run_query(query, {'cod_nacion': cod_nacion})

    def get_shortest_path(self, cod1: str, cod2: str) -> List[Dict]:
        """Find shortest interaction path between two drugs."""
        query = """
        MATCH path = shortestPath(
            (d1:Drug {cod_nacion: $cod1})-[:INTERACTS_WITH_ATC*]-(d2:Drug {cod_nacion: $cod2})
        )
        RETURN [node in nodes(path) |
            CASE WHEN node:Drug THEN node.nombre_comercial
                 ELSE node.codigo END] AS drug_path,
               length(path) AS path_length
        """
        return self._run_query(query, {'cod1': cod1, 'cod2': cod2})

    def get_drugs_by_ingredient(self, ingredient_name: str) -> List[Dict]:
        """Find drugs containing a specific ingredient via graph."""
        query = """
        MATCH (d:Drug)-[:CONTAINS]->(i:ActiveIngredient)
        WHERE i.nombre CONTAINS $name
        RETURN DISTINCT d.cod_nacion AS cod_nacion,
               d.nombre_comercial AS nombre,
               i.nombre AS ingredient
        LIMIT 100
        """
        return self._run_query(query, {'name': ingredient_name})

    def get_top_interacting_drugs(self, limit: int = 10) -> List[Dict]:
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
