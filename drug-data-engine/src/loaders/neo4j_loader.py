"""
Neo4J Loader for drug interaction graph database.
Handles connection, constraint creation, and data loading.
"""
from typing import List, Dict, Any, Optional
import logging
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable, AuthError

logger = logging.getLogger(__name__)


class Neo4JLoader:
    """Loader for Neo4J graph database."""

    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize the Neo4J loader.

        Args:
            uri: Neo4J connection URI
            user: Neo4J username
            password: Neo4J password
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.driver: Optional[Driver] = None

    def connect(self) -> bool:
        """
        Connect to Neo4J.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to Neo4J...")
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )

            # Verify connection
            self.driver.verify_connectivity()

            logger.info("Connected to Neo4J")
            return True
        except ServiceUnavailable as e:
            logger.error(f"Neo4J service unavailable: {e}")
            return False
        except AuthError as e:
            logger.error(f"Neo4J authentication failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Neo4J: {e}")
            return False

    def disconnect(self):
        """Disconnect from Neo4J."""
        if self.driver:
            self.driver.close()
            logger.info("Disconnected from Neo4J")

    def setup_constraints_and_indexes(self):
        """Create constraints and indexes."""
        if self.driver is None:
            raise ValueError("Not connected to database. Call connect() first.")

        logger.info("Setting up Neo4J constraints and indexes...")

        constraints = [
            # Unique constraints
            "CREATE CONSTRAINT drug_cod_nacion IF NOT EXISTS FOR (d:Drug) REQUIRE d.cod_nacion IS UNIQUE",
            "CREATE CONSTRAINT ingredient_codigo IF NOT EXISTS FOR (a:ActiveIngredient) REQUIRE a.codigo IS UNIQUE",
            "CREATE CONSTRAINT lab_codigo IF NOT EXISTS FOR (l:Laboratory) REQUIRE l.codigo IS UNIQUE",
            "CREATE CONSTRAINT atc_codigo IF NOT EXISTS FOR (a:ATCCode) REQUIRE a.codigo IS UNIQUE",
            "CREATE CONSTRAINT form_codigo IF NOT EXISTS FOR (p:PharmaceuticalForm) REQUIRE p.codigo IS UNIQUE",
            "CREATE CONSTRAINT route_codigo IF NOT EXISTS FOR (r:AdministrationRoute) REQUIRE r.codigo IS UNIQUE",
            "CREATE CONSTRAINT excipient_codigo IF NOT EXISTS FOR (e:Excipient) REQUIRE e.codigo IS UNIQUE",
            "CREATE CONSTRAINT package_codigo IF NOT EXISTS FOR (p:PackageType) REQUIRE p.codigo IS UNIQUE",
            "CREATE CONSTRAINT biomarker_marcador IF NOT EXISTS FOR (b:Biomarker) REQUIRE b.marcador IS UNIQUE",
        ]

        indexes = [
            # Performance indexes
            "CREATE INDEX drug_nombre IF NOT EXISTS FOR (d:Drug) ON (d.nombre_comercial)",
            "CREATE INDEX drug_generico IF NOT EXISTS FOR (d:Drug) ON (d.es_generico)",
            "CREATE INDEX drug_comercializado IF NOT EXISTS FOR (d:Drug) ON (d.comercializado)",
            "CREATE INDEX drug_uso_hospitalario IF NOT EXISTS FOR (d:Drug) ON (d.uso_hospitalario)",
            "CREATE INDEX ingredient_nombre IF NOT EXISTS FOR (a:ActiveIngredient) ON (a.nombre)",
            "CREATE INDEX atc_descripcion IF NOT EXISTS FOR (a:ATCCode) ON (a.descripcion)",
        ]

        with self.driver.session() as session:
            for query in constraints + indexes:
                try:
                    session.run(query)
                except Exception as e:
                    logger.warning(f"Could not create constraint/index: {e}")

        logger.info("Constraints and indexes created successfully")

    def clear_database(self):
        """Clear all nodes and relationships from the database."""
        if self.driver is None:
            raise ValueError("Not connected to database.")

        logger.info("Clearing Neo4J database...")

        with self.driver.session() as session:
            # Delete in batches to avoid memory issues
            while True:
                result = session.run(
                    "MATCH (n) WITH n LIMIT 10000 DETACH DELETE n RETURN count(*) as deleted"
                )
                deleted = result.single()['deleted']
                if deleted == 0:
                    break
                logger.info(f"Deleted {deleted} nodes...")

        logger.info("Neo4J database cleared")

    def load_active_ingredients(self, ingredients: List[Dict]):
        """Load active ingredients as nodes."""
        if self.driver is None:
            raise ValueError("Not connected to database.")

        logger.info(f"Loading {len(ingredients)} active ingredients...")

        query = """
        UNWIND $batch AS item
        MERGE (a:ActiveIngredient {codigo: item.codigo})
        SET a.nombre = item.nombre,
            a.codigo_aemps = item.codigo_aemps,
            a.lista_psicotropo = item.lista_psicotropo
        """

        self._batch_write(query, ingredients)
        logger.info("Active ingredients loaded")

    def load_laboratories(self, laboratories: List[Dict]):
        """Load laboratories as nodes."""
        if self.driver is None:
            raise ValueError("Not connected to database.")

        logger.info(f"Loading {len(laboratories)} laboratories...")

        query = """
        UNWIND $batch AS item
        MERGE (l:Laboratory {codigo: item.codigo})
        SET l.nombre = item.nombre,
            l.direccion = item.direccion,
            l.codigo_postal = item.codigo_postal,
            l.localidad = item.localidad,
            l.cif = item.cif
        """

        self._batch_write(query, laboratories)
        logger.info("Laboratories loaded")

    def load_atc_codes(self, atc_codes: List[Dict]):
        """Load ATC codes as nodes."""
        if self.driver is None:
            raise ValueError("Not connected to database.")

        logger.info(f"Loading {len(atc_codes)} ATC codes...")

        query = """
        UNWIND $batch AS item
        MERGE (a:ATCCode {codigo: item.codigo})
        SET a.nro = item.nro,
            a.descripcion = item.descripcion,
            a.nivel = size(item.codigo)
        """

        self._batch_write(query, atc_codes)
        logger.info("ATC codes loaded")

    def load_atc_hierarchy(self, hierarchy: List[Dict]):
        """Load ATC hierarchy relationships."""
        if self.driver is None:
            raise ValueError("Not connected to database.")

        logger.info(f"Loading {len(hierarchy)} ATC hierarchy relationships...")

        query = """
        UNWIND $batch AS item
        MATCH (parent:ATCCode {codigo: item.parent})
        MATCH (child:ATCCode {codigo: item.child})
        MERGE (parent)-[:PARENT_OF]->(child)
        """

        self._batch_write(query, hierarchy)
        logger.info("ATC hierarchy loaded")

    def load_pharmaceutical_forms(self, forms: List[Dict]):
        """Load pharmaceutical forms as nodes."""
        if self.driver is None:
            raise ValueError("Not connected to database.")

        logger.info(f"Loading {len(forms)} pharmaceutical forms...")

        query = """
        UNWIND $batch AS item
        MERGE (p:PharmaceuticalForm {codigo: item.codigo})
        SET p.nombre = item.nombre,
            p.codigo_simplificado = item.codigo_simplificado
        """

        self._batch_write(query, forms)
        logger.info("Pharmaceutical forms loaded")

    def load_administration_routes(self, routes: List[Dict]):
        """Load administration routes as nodes."""
        if self.driver is None:
            raise ValueError("Not connected to database.")

        logger.info(f"Loading {len(routes)} administration routes...")

        query = """
        UNWIND $batch AS item
        MERGE (r:AdministrationRoute {codigo: item.codigo})
        SET r.nombre = item.nombre
        """

        self._batch_write(query, routes)
        logger.info("Administration routes loaded")

    def load_excipients(self, excipients: List[Dict]):
        """Load excipients as nodes."""
        if self.driver is None:
            raise ValueError("Not connected to database.")

        logger.info(f"Loading {len(excipients)} excipients...")

        query = """
        UNWIND $batch AS item
        MERGE (e:Excipient {codigo: item.codigo})
        SET e.nombre = item.nombre
        """

        self._batch_write(query, excipients)
        logger.info("Excipients loaded")

    def load_package_types(self, packages: List[Dict]):
        """Load package types as nodes."""
        if self.driver is None:
            raise ValueError("Not connected to database.")

        logger.info(f"Loading {len(packages)} package types...")

        query = """
        UNWIND $batch AS item
        MERGE (p:PackageType {codigo: item.codigo})
        SET p.nombre = item.nombre
        """

        self._batch_write(query, packages)
        logger.info("Package types loaded")

    def load_biomarkers(self, drugs: List[Dict]):
        """
        Load Biomarker nodes extracted from drug data.

        Biomarkers are not in a separate dictionary file — they are embedded
        in each drug's data. This method collects unique biomarkers across
        all drugs and creates them as nodes.
        """
        if self.driver is None:
            raise ValueError("Not connected to database.")

        # Collect unique biomarkers from all drugs
        unique_biomarkers = {}
        for drug in drugs:
            for bio in drug['relationships']['biomarkers']:
                marcador = bio['marcador']
                if marcador and marcador not in unique_biomarkers:
                    unique_biomarkers[marcador] = {
                        'marcador': marcador,
                        'clase': bio.get('clase', ''),
                    }

        if not unique_biomarkers:
            logger.info("No biomarkers found in drug data")
            return

        biomarker_list = list(unique_biomarkers.values())
        logger.info(f"Loading {len(biomarker_list)} unique biomarkers...")

        query = """
        UNWIND $batch AS item
        MERGE (b:Biomarker {marcador: item.marcador})
        SET b.clase = item.clase
        """

        self._batch_write(query, biomarker_list)
        logger.info("Biomarker nodes loaded")

    def load_drugs(self, drugs: List[Dict]):
        """Load drug nodes."""
        if self.driver is None:
            raise ValueError("Not connected to database.")

        logger.info(f"Loading {len(drugs)} drugs...")

        query = """
        UNWIND $batch AS item
        MERGE (d:Drug {cod_nacion: item.node.cod_nacion})
        SET d += item.node
        """

        self._batch_write(query, drugs)
        logger.info("Drug nodes loaded")

    def load_drug_relationships(self, drugs: List[Dict]):
        """Load drug relationships."""
        if self.driver is None:
            raise ValueError("Not connected to database.")

        logger.info(f"Loading relationships for {len(drugs)} drugs...")

        # Manufactured by
        query_manufactured = """
        UNWIND $batch AS item
        MATCH (d:Drug {cod_nacion: item.node.cod_nacion})
        MATCH (l:Laboratory {codigo: item.relationships.manufactured_by})
        MERGE (d)-[:MANUFACTURED_BY]->(l)
        """

        # Marketed by
        query_marketed = """
        UNWIND $batch AS item
        MATCH (d:Drug {cod_nacion: item.node.cod_nacion})
        MATCH (l:Laboratory {codigo: item.relationships.marketed_by})
        MERGE (d)-[:MARKETED_BY]->(l)
        """

        # Classified as ATC
        query_atc = """
        UNWIND $batch AS item
        MATCH (d:Drug {cod_nacion: item.node.cod_nacion})
        MATCH (a:ATCCode {codigo: item.relationships.atc_code})
        MERGE (d)-[:CLASSIFIED_AS]->(a)
        """

        # Contains active ingredients
        query_contains = """
        UNWIND $batch AS item
        MATCH (d:Drug {cod_nacion: item.node.cod_nacion})
        UNWIND item.relationships.contains AS ing
        MATCH (a:ActiveIngredient {codigo: ing.codigo})
        MERGE (d)-[r:CONTAINS]->(a)
        SET r.orden = ing.orden,
            r.dosis = ing.dosis,
            r.unidad_dosis = ing.unidad_dosis,
            r.dosis_prescripcion = ing.dosis_prescripcion,
            r.unidad_prescripcion = ing.unidad_prescripcion
        """

        # Has pharmaceutical form
        query_form = """
        UNWIND $batch AS item
        MATCH (d:Drug {cod_nacion: item.node.cod_nacion})
        UNWIND item.relationships.has_form AS form_code
        MATCH (p:PharmaceuticalForm {codigo: form_code})
        MERGE (d)-[:HAS_FORM]->(p)
        """

        # Administered via
        query_route = """
        UNWIND $batch AS item
        MATCH (d:Drug {cod_nacion: item.node.cod_nacion})
        UNWIND item.relationships.administered_via AS route_code
        MATCH (r:AdministrationRoute {codigo: route_code})
        MERGE (d)-[:ADMINISTERED_VIA]->(r)
        """

        # Packaged in
        query_package = """
        UNWIND $batch AS item
        MATCH (d:Drug {cod_nacion: item.node.cod_nacion})
        MATCH (p:PackageType {codigo: item.relationships.packaged_in})
        MERGE (d)-[:PACKAGED_IN]->(p)
        """

        # Contains excipients
        query_excipient = """
        UNWIND $batch AS item
        MATCH (d:Drug {cod_nacion: item.node.cod_nacion})
        UNWIND item.relationships.contains_excipient AS exc_code
        MATCH (e:Excipient {codigo: exc_code})
        MERGE (d)-[:CONTAINS_EXCIPIENT]->(e)
        """

        # Has biomarker
        query_biomarker = """
        UNWIND $batch AS item
        MATCH (d:Drug {cod_nacion: item.node.cod_nacion})
        UNWIND item.relationships.biomarkers AS bio
        MATCH (b:Biomarker {marcador: bio.marcador})
        MERGE (d)-[r:HAS_BIOMARKER]->(b)
        SET r.genotipo_fenotipo = bio.genotipo_fenotipo,
            r.notas = bio.notas
        """

        # Filter drugs with valid relationships
        drugs_with_lab = [d for d in drugs if d['relationships']['manufactured_by']]
        drugs_with_marketed = [d for d in drugs if d['relationships']['marketed_by']]
        drugs_with_atc = [d for d in drugs if d['relationships']['atc_code']]
        drugs_with_contains = [d for d in drugs if d['relationships']['contains']]
        drugs_with_form = [d for d in drugs if d['relationships']['has_form']]
        drugs_with_route = [d for d in drugs if d['relationships']['administered_via']]
        drugs_with_package = [d for d in drugs if d['relationships']['packaged_in']]
        drugs_with_excipient = [d for d in drugs if d['relationships']['contains_excipient']]
        drugs_with_biomarker = [d for d in drugs if d['relationships']['biomarkers']]

        self._batch_write(query_manufactured, drugs_with_lab)
        self._batch_write(query_marketed, drugs_with_marketed)
        self._batch_write(query_atc, drugs_with_atc)
        self._batch_write(query_contains, drugs_with_contains)
        self._batch_write(query_form, drugs_with_form)
        self._batch_write(query_route, drugs_with_route)
        self._batch_write(query_package, drugs_with_package)
        self._batch_write(query_excipient, drugs_with_excipient)
        self._batch_write(query_biomarker, drugs_with_biomarker)

        logger.info("Drug relationships loaded")

    def load_drug_interactions(self, drugs: List[Dict]):
        """Load drug interaction relationships."""
        if self.driver is None:
            raise ValueError("Not connected to database.")

        # Filter drugs with interactions
        drugs_with_interactions = [d for d in drugs if d['relationships']['interactions']]

        if not drugs_with_interactions:
            logger.info("No drug interactions to load")
            return

        logger.info(f"Loading interactions for {len(drugs_with_interactions)} drugs...")

        # Interactions with ATC codes
        query = """
        UNWIND $batch AS item
        MATCH (d:Drug {cod_nacion: item.node.cod_nacion})
        UNWIND item.relationships.interactions AS int
        MATCH (a:ATCCode {codigo: int.atc_destino})
        MERGE (d)-[r:INTERACTS_WITH_ATC]->(a)
        SET r.medicamento_nombre = int.nombre_destino,
            r.efecto = int.efecto,
            r.recomendacion = int.recomendacion,
            r.procesado_nlp = false
        """

        self._batch_write(query, drugs_with_interactions)
        logger.info("Drug interactions loaded")

    def _batch_write(self, query: str, data: List[Dict], batch_size: int = 500):
        """Execute a write query in batches."""
        if not data:
            return

        with self.driver.session() as session:
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                session.run(query, batch=batch)

                if (i + batch_size) % 2000 == 0:
                    logger.info(f"Processed {i + batch_size} items...")

    def get_stats(self) -> Dict[str, int]:
        """Get node and relationship counts."""
        if self.driver is None:
            raise ValueError("Not connected to database.")

        stats = {}

        with self.driver.session() as session:
            # Node counts
            for label in ['Drug', 'ActiveIngredient', 'Laboratory', 'ATCCode',
                         'PharmaceuticalForm', 'AdministrationRoute', 'Excipient',
                         'PackageType', 'Biomarker']:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                stats[f"nodes_{label}"] = result.single()['count']

            # Relationship counts
            for rel_type in ['MANUFACTURED_BY', 'MARKETED_BY', 'CLASSIFIED_AS',
                            'CONTAINS', 'HAS_FORM', 'ADMINISTERED_VIA',
                            'PACKAGED_IN', 'CONTAINS_EXCIPIENT',
                            'HAS_BIOMARKER', 'INTERACTS_WITH_ATC', 'PARENT_OF']:
                result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                stats[f"rels_{rel_type}"] = result.single()['count']

        return stats
