# python -m app.loader.neo4j_loader

import os
import csv
from neo4j import GraphDatabase
import logging
from app.core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Neo4j configuration
NEO4J_URI = settings.neo4j_uri
NEO4J_USER = settings.neo4j_user
NEO4J_PASSWORD = settings.neo4j_password

CSV_DIR = None
possible_paths = [
    os.path.join(os.getcwd(), 'data', 'csv', 'csv2'),
    os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'csv', 'csv2'),
    os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '../../../data/csv/csv2')),
    r'C:\Users\mserb\Desktop\UMA\Trabajo Fin de Máster\data\csv\csv2'
]

for path in possible_paths:
    abs_path = os.path.abspath(path)
    if os.path.exists(abs_path):
        CSV_DIR = abs_path
        break

if CSV_DIR is None:
    raise FileNotFoundError("Could not find CSV directory. Please check the path configuration.")

logger.info(f"Using CSV directory: {CSV_DIR}")


class Neo4jLoader:
    def __init__(self, uri, user, password):
        """Initialize Neo4j connection"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info("Initialized Neo4j connection to %s", uri)

    def close(self):
        """Close Neo4j connection"""
        self.driver.close()
        logger.info("Closed Neo4j connection")

    def run_query(self, query, parameters=None):
        """Execute a Cypher query"""
        with self.driver.session() as session:
            try:
                result = session.run(query, parameters or {})
                # Consume results to ensure query execution completes
                summary = result.consume()
                logger.info(f"Query executed: {summary.counters}")
                return True
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                return False

    def read_csv_file(self, file_path):
        """Read CSV file and return rows as list of dictionaries"""
        rows = []
        try:
            logger.info(f"Attempting to read CSV file: {file_path}")

            if not os.path.exists(file_path):
                logger.error(f"File does not exist: {file_path}")
                return []

            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as csvfile:
                        reader = csv.DictReader(csvfile)
                        rows = list(reader)
                        logger.info(f"Successfully read {len(rows)} rows from {file_path} using {encoding} encoding")

                        # Log the column headers for debugging
                        if rows:
                            logger.info(f"CSV columns: {list(rows[0].keys())}")

                        return rows
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"Error reading with {encoding} encoding: {e}")
                    continue

            logger.error(f"Could not read file with any encoding: {file_path}")
            return []

        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {e}")
            return []

    def batch_create_nodes(self, query, data, batch_size=1000):
        """Create nodes in batches for better performance"""
        if not data:
            logger.warning("No data provided for batch creation")
            return False

        total_rows = len(data)
        logger.info(f"Creating {total_rows} nodes in batches of {batch_size}")

        with self.driver.session() as session:
            for i in range(0, total_rows, batch_size):
                batch = data[i:i + batch_size]
                try:
                    result = session.run(query, {"batch": batch})
                    summary = result.consume()
                    logger.info(f"Processed batch {i // batch_size + 1} / {(total_rows - 1) // batch_size + 1} - Created: {summary.counters.nodes_created}") # noqa
                except Exception as e:
                    logger.error(f"Error processing batch {i // batch_size + 1}: {e}")
                    return False
        return True

    def load_all_nodes(self):
        """Load all nodes from CSV files into Neo4j"""
        # Ensure CSV paths are correct
        csv_paths = {
            "ATC": "DICCIONARIO_ATC.csv",
            "DCP": "DICCIONARIO_DCP.csv",
            "DCPF": "DICCIONARIO_DCPF.csv",
            "DCSA": "DICCIONARIO_DCSA.csv",
            "Envases": "DICCIONARIO_ENVASES.csv",
            "Excipientes": "DICCIONARIO_EXCIPIENTES_DECL_OBLIGATORIA.csv",
            "FormaFarmaceuticaSimplificada": "DICCIONARIO_FORMA_FARMACEUTICA_SIMPLIFICADAS.csv",
            "FormaFarmaceutica": "DICCIONARIO_FORMA_FARMACEUTICA.csv",
            "Laboratorios": "DICCIONARIO_LABORATORIOS.csv",
            "PrincipiosActivos": "DICCIONARIO_PRINCIPIOS_ACTIVOS.csv",
            "SituacionRegistro": "DICCIONARIO_SITUACION_REGISTRO.csv",
            "UnidadContenido": "DICCIONARIO_UNIDAD_CONTENIDO.csv",
            "ViasAdministracion": "DICCIONARIO_VIAS_ADMINISTRACION.csv",
            "Prescripcion": "PRESCRIPCION.csv",
            "PrescripcionComposicion": "PRESCRIPCION_COMPOSICION.csv",
            "PrescripcionATCDuplicidades": "PRESCRIPCION_ATC_DUPLICIDADES.csv"
        }

        # Execute queries to create nodes
        self._create_atc_nodes(os.path.join(CSV_DIR, csv_paths["ATC"]))
        self._create_dcp_nodes(os.path.join(CSV_DIR, csv_paths["DCP"]))
        self._create_dcpf_nodes(os.path.join(CSV_DIR, csv_paths["DCPF"]))
        self._create_dcsa_nodes(os.path.join(CSV_DIR, csv_paths["DCSA"]))
        self._create_envases_nodes(os.path.join(CSV_DIR, csv_paths["Envases"]))
        self._create_excipientes_nodes(os.path.join(CSV_DIR, csv_paths["Excipientes"]))
        self._create_forma_farmaceutica_simplificada_nodes(os.path.join(CSV_DIR, csv_paths["FormaFarmaceuticaSimplificada"]))
        self._create_forma_farmaceutica_nodes(os.path.join(CSV_DIR, csv_paths["FormaFarmaceutica"]))
        self._create_laboratorios_nodes(os.path.join(CSV_DIR, csv_paths["Laboratorios"]))
        self._create_principios_activos_nodes(os.path.join(CSV_DIR, csv_paths["PrincipiosActivos"]))
        self._create_situacion_registro_nodes(os.path.join(CSV_DIR, csv_paths["SituacionRegistro"]))
        self._create_unidad_contenido_nodes(os.path.join(CSV_DIR, csv_paths["UnidadContenido"]))
        self._create_vias_administracion_nodes(os.path.join(CSV_DIR, csv_paths["ViasAdministracion"]))
        self._create_prescripcion_nodes(os.path.join(CSV_DIR, csv_paths["Prescripcion"]))
        self._create_composicion_nodes(os.path.join(CSV_DIR, csv_paths["PrescripcionComposicion"]))
        self._create_duplicidad_nodes(os.path.join(CSV_DIR, csv_paths["PrescripcionATCDuplicidades"]))

    def _create_atc_nodes(self, file_path):
        """Create ATC nodes"""
        logger.info("Creating ATC nodes from %s", file_path)
        data = self.read_csv_file(file_path)
        if not data:
            return False

        query = """
        UNWIND $batch AS row
        CREATE (atc:ATC {
            nroatc: row.nroatc,
            codigoatc: row.codigoatc,
            descatc: row.descatc
        })
        """
        return self.batch_create_nodes(query, data)

    def _create_dcp_nodes(self, file_path):
        """Create DCP nodes"""
        logger.info("Creating DCP nodes from %s", file_path)
        data = self.read_csv_file(file_path)
        if not data:
            return False

        query = """
        UNWIND $batch AS row
        CREATE (dcp:DCP {
            codigodcp: row.codigodcp,
            nombredcp: row.nombredcp,
            codigodcsa: row.codigodcsa
        })
        """
        return self.batch_create_nodes(query, data)

    def _create_dcpf_nodes(self, file_path):
        """Create DCPF nodes"""
        logger.info("Creating DCPF nodes from %s", file_path)
        data = self.read_csv_file(file_path)
        if not data:
            return False

        query = """
        UNWIND $batch AS row
        CREATE (dcpf:DCPF {
            codigodcpf: row.codigodcpf,
            nombredcpf: row.nombredcpf,
            codigodcp: row.codigodcp
        })
        """
        return self.batch_create_nodes(query, data)

    def _create_dcsa_nodes(self, file_path):
        """Create DCSA nodes"""
        logger.info("Creating DCSA nodes from %s", file_path)
        data = self.read_csv_file(file_path)
        if not data:
            return False

        query = """
        UNWIND $batch AS row
        CREATE (dcsa:DCSA {
            codigodcsa: row.codigodcsa,
            nombredcsa: row.nombredcsa
        })
        """
        return self.batch_create_nodes(query, data)

    def _create_envases_nodes(self, file_path):
        """Create Envase nodes"""
        logger.info("Creating Envase nodes from %s", file_path)
        data = self.read_csv_file(file_path)
        if not data:
            return False

        query = """
        UNWIND $batch AS row
        CREATE (envase:Envase {
            codigoenvase: row.codigoenvase,
            envase: row.envase
        })
        """
        return self.batch_create_nodes(query, data)

    def _create_excipientes_nodes(self, file_path):
        """Create Excipiente nodes"""
        logger.info("Creating Excipiente nodes from %s", file_path)
        data = self.read_csv_file(file_path)
        if not data:
            return False

        query = """
        UNWIND $batch AS row
        CREATE (excipiente:Excipiente {
            codigoedo: row.codigoedo,
            edo: row.edo
        })
        """
        return self.batch_create_nodes(query, data)

    def _create_forma_farmaceutica_simplificada_nodes(self, file_path):
        """Create FormaFarmaceuticaSimplificada nodes"""
        logger.info("Creating FormaFarmaceuticaSimplificada nodes from %s", file_path)
        data = self.read_csv_file(file_path)
        if not data:
            return False

        query = """
        UNWIND $batch AS row
        CREATE (formaSimpli:FormaFarmaceuticaSimplificada {
            codigoformafarmaceuticasimplificada: row.codigoformafarmaceuticasimplificada,
            formafarmaceuticasimplificada: row.formafarmaceuticasimplificada
        })
        """
        return self.batch_create_nodes(query, data)

    def _create_forma_farmaceutica_nodes(self, file_path):
        """Create FormaFarmaceutica nodes"""
        logger.info("Creating FormaFarmaceutica nodes from %s", file_path)
        data = self.read_csv_file(file_path)
        if not data:
            return False

        query = """
        UNWIND $batch AS row
        CREATE (forma:FormaFarmaceutica {
            codigoformafarmaceutica: row.codigoformafarmaceutica,
            formafarmaceutica: row.formafarmaceutica,
            codigoformafarmaceuticasimplificada: row.codigoformafarmaceuticasimplificada
        })
        """
        return self.batch_create_nodes(query, data)

    def _create_laboratorios_nodes(self, file_path):
        """Create Laboratorio nodes"""
        logger.info("Creating Laboratorio nodes from %s", file_path)
        data = self.read_csv_file(file_path)
        if not data:
            return False

        query = """
        UNWIND $batch AS row
        CREATE (lab:Laboratorio {
            codigolaboratorio: row.codigolaboratorio,
            laboratorio: row.laboratorio,
            direccion: row.direccion,
            codigopostal: row.codigopostal,
            localidad: row.localidad,
            cif: row.cif
        })
        """
        return self.batch_create_nodes(query, data)

    def _create_principios_activos_nodes(self, file_path):
        """Create PrincipioActivo nodes"""
        logger.info("Creating PrincipioActivo nodes from %s", file_path)
        data = self.read_csv_file(file_path)
        if not data:
            return False

        query = """
        UNWIND $batch AS row
        CREATE (principio:PrincipioActivo {
            nroprincipioactivo: row.nroprincipioactivo,
            codigoprincipioactivo: row.codigoprincipioactivo,
            principioactivo: row.principioactivo
        })
        """
        return self.batch_create_nodes(query, data)

    def _create_situacion_registro_nodes(self, file_path):
        """Create SituacionRegistro nodes"""
        logger.info("Creating SituacionRegistro nodes from %s", file_path)
        data = self.read_csv_file(file_path)
        if not data:
            return False

        query = """
        UNWIND $batch AS row
        CREATE (sitreg:SituacionRegistro {
            codigosituacionregistro: row.codigosituacionregistro,
            situacionregistro: row.situacionregistro
        })
        """
        return self.batch_create_nodes(query, data)

    def _create_unidad_contenido_nodes(self, file_path):
        """Create UnidadContenido nodes"""
        logger.info("Creating UnidadContenido nodes from %s", file_path)
        data = self.read_csv_file(file_path)
        if not data:
            return False

        query = """
        UNWIND $batch AS row
        CREATE (unidad:UnidadContenido {
            codigounidadcontenido: row.codigounidadcontenido,
            unidadcontenido: row.unidadcontenido
        })
        """
        return self.batch_create_nodes(query, data)

    def _create_vias_administracion_nodes(self, file_path):
        """Create ViaAdministracion nodes"""
        logger.info("Creating ViaAdministracion nodes from %s", file_path)
        data = self.read_csv_file(file_path)
        if not data:
            return False

        query = """
        UNWIND $batch AS row
        CREATE (via:ViaAdministracion {
            codigoviaadministracion: row.codigoviaadministracion,
            viaadministracion: row.viaadministracion
        })
        """
        return self.batch_create_nodes(query, data)

    def _create_prescripcion_nodes(self, file_path):
        """Create Prescripcion nodes"""
        logger.info("Creating Prescripcion nodes from %s", file_path)
        data = self.read_csv_file(file_path)
        if not data:
            return False

        query = """
        UNWIND $batch AS row
        CREATE (p:Prescripcion {
            cod_nacion: row.cod_nacion,
            nro_definitivo: row.nro_definitivo,
            des_nomco: row.des_nomco,
            cod_dcp: row.cod_dcp,
            cod_dcpf: row.cod_dcpf,
            cod_dcsa: row.cod_dcsa,
            cod_viaadmin: row.cod_viaadmin,
            cod_envase: row.cod_envase,
            contenido: row.contenido,
            unid_contenido: row.unid_contenido,
            laboratorio_titular: row.laboratorio_titular,
            fecha_autorizacion: row.fecha_autorizacion,
            cod_sitreg: row.cod_sitreg,
            sw_generico: row.sw_generico,
            url_fictec: row.url_fictec
        })
        """
        return self.batch_create_nodes(query, data)

    def _create_composicion_nodes(self, file_path):
        """Create Composicion nodes"""
        logger.info("Creating Composicion nodes from %s", file_path)
        data = self.read_csv_file(file_path)
        if not data:
            return False

        query = """
        UNWIND $batch AS row
        CREATE (comp:Composicion {
            nro_definitivo: row.nro_definitivo,
            cod_principio_activo: row.cod_principio_activo,
            orden_colacion: row.orden_colacion,
            dosis_pa: row.dosis_pa,
            unidad_dosis_pa: row.unidad_dosis_pa,
            dosis_composicion: row.dosis_composicion,
            unidad_composicion: row.unidad_composicion,
            dosis_administracion: row.dosis_administracion,
            unidad_administracion: row.unidad_administracion,
            dosis_prescripcion: row.dosis_prescripcion,
            unidad_prescripcion: row.unidad_prescripcion
        })
        """
        return self.batch_create_nodes(query, data)

    def _create_duplicidad_nodes(self, file_path):
        """Create Duplicidad nodes"""
        logger.info("Creating Duplicidad nodes from %s", file_path)
        data = self.read_csv_file(file_path)
        if not data:
            return False

        query = """
        UNWIND $batch AS row
        CREATE (dup:Duplicidad {
            nro_definitivo: row.nro_definitivo,
            cod_atc: row.cod_atc,
            atc_duplicidad: row.atc_duplicidad,
            descripcion: row.descripcion,
            efecto: row.efecto,
            recomendacion: row.recomendacion
        })
        """
        return self.batch_create_nodes(query, data)

    def create_all_relationships(self):
        """Create all relationships between nodes in Neo4j"""
        logger.info("Creating relationships between nodes")

        # Create indexes first for better performance
        self.create_indexes()

        # 1. Connect DCPF to DCP (Package to Product Definition)
        logger.info("Creating relationships: DCPF to DCP")
        query = """
        MATCH (dcpf:DCPF), (dcp:DCP)
        WHERE dcpf.codigodcp = dcp.codigodcp
        CREATE (dcpf)-[:BELONGS_TO]->(dcp)
        """
        self.run_query(query)

        # 2. Connect DCP to DCSA (Product Definition to Active Substance)
        logger.info("Creating relationships: DCP to DCSA")
        query = """
        MATCH (dcp:DCP), (dcsa:DCSA)
        WHERE dcp.codigodcsa = dcsa.codigodcsa
        CREATE (dcp)-[:CONTAINS_SUBSTANCE]->(dcsa)
        """
        self.run_query(query)

        # 3. Connect Prescription to DCP & DCPF
        logger.info("Creating relationships: Prescription to DCP & DCPF")
        query = """
        MATCH (p:Prescripcion), (dcp:DCP)
        WHERE p.cod_dcp = dcp.codigodcp
        CREATE (p)-[:HAS_DEFINITION]->(dcp)
        """
        self.run_query(query)

        query = """
        MATCH (p:Prescripcion), (dcpf:DCPF)
        WHERE p.cod_dcpf = dcpf.codigodcpf
        CREATE (p)-[:HAS_PACKAGE]->(dcpf)
        """
        self.run_query(query)

        # 4. Connect Prescription to DCSA (Active Substance)
        logger.info("Creating relationships: Prescription to DCSA")
        query = """
        MATCH (p:Prescripcion), (dcsa:DCSA)
        WHERE p.cod_dcsa = dcsa.codigodcsa
        CREATE (p)-[:CONTAINS_SUBSTANCE]->(dcsa)
        """
        self.run_query(query)

        # 5. Connect Prescription to Container Type
        logger.info("Creating relationships: Prescription to Container Type")
        query = """
        MATCH (p:Prescripcion), (e:Envase)
        WHERE p.cod_envase = e.codigoenvase
        CREATE (p)-[:HAS_CONTAINER]->(e)
        """
        self.run_query(query)

        # 6. Connect Prescription to Content Unit
        logger.info("Creating relationships: Prescription to Content Unit")
        query = """
        MATCH (p:Prescripcion), (u:UnidadContenido)
        WHERE p.unid_contenido = u.codigounidadcontenido
        CREATE (p)-[:HAS_CONTENT_UNIT]->(u)
        """
        self.run_query(query)

        # 7. Connect Prescription to Laboratory
        logger.info("Creating relationships: Prescription to Laboratory")
        query = """
        MATCH (p:Prescripcion), (lab:Laboratorio)
        WHERE p.laboratorio_titular = lab.codigolaboratorio
        CREATE (p)-[:MANUFACTURED_BY]->(lab)
        """
        self.run_query(query)

        # 8. Connect Prescription to Registration Status
        logger.info("Creating relationships: Prescription to Registration Status")
        query = """
        MATCH (p:Prescripcion), (sr:SituacionRegistro)
        WHERE p.cod_sitreg = sr.codigosituacionregistro
        CREATE (p)-[:HAS_STATUS]->(sr)
        """
        self.run_query(query)

        # 9. Connect Composition to Prescription
        logger.info("Creating relationships: Composition to Prescription")
        query = """
        MATCH (comp:Composicion), (p:Prescripcion)
        WHERE comp.nro_definitivo = p.nro_definitivo
        CREATE (comp)-[:PART_OF]->(p)
        """
        self.run_query(query)

        # 10. Connect Composition to Active Ingredient
        logger.info("Creating relationships: Composition to Active Ingredient")
        query = """
        MATCH (comp:Composicion), (pa:PrincipioActivo)
        WHERE comp.cod_principio_activo = pa.codigoprincipioactivo
        CREATE (comp)-[:USES_INGREDIENT]->(pa)
        """
        self.run_query(query)

        # 11. Connect ATC Duplicities to Prescription
        logger.info("Creating relationships: ATC Duplicities to Prescription")
        query = """
        MATCH (dup:Duplicidad), (p:Prescripcion)
        WHERE dup.nro_definitivo = p.nro_definitivo
        CREATE (dup)-[:RELATES_TO]->(p)
        """
        self.run_query(query)

        # 12. Connect ATC Duplicities to ATC codes
        logger.info("Creating relationships: ATC Duplicities to ATC codes")
        query = """
        MATCH (dup:Duplicidad), (atc:ATC)
        WHERE dup.cod_atc = atc.codigoatc
        CREATE (dup)-[:REFERENCES_CODE]->(atc)
        """
        self.run_query(query)

        query = """
        MATCH (dup:Duplicidad), (atc:ATC)
        WHERE dup.atc_duplicidad = atc.codigoatc
        CREATE (dup)-[:DUPLICATES_CODE]->(atc)
        """
        self.run_query(query)

        # 13. Connect Pharmaceutical Form to Simplified Form
        logger.info("Creating relationships: Pharmaceutical Form to Simplified Form")
        query = """
        MATCH (ff:FormaFarmaceutica), (ffs:FormaFarmaceuticaSimplificada)
        WHERE ff.codigoformafarmaceuticasimplificada = ffs.codigoformafarmaceuticasimplificada
        CREATE (ff)-[:SIMPLIFIED_AS]->(ffs)
        """
        self.run_query(query)

        # 14. Connect Prescription to Administration Route
        logger.info("Creating relationships: Prescription to Administration Route")
        query = """
        MATCH (p:Prescripcion), (v:ViaAdministracion)
        WHERE p.cod_viaadmin = v.codigoviaadministracion
        CREATE (p)-[:HAS_ADMIN_ROUTE]->(v)
        """
        self.run_query(query)

        logger.info("All relationships created successfully")

    def create_indexes(self):
        """Create indexes for better query performance"""
        logger.info("Creating indexes for better performance")

        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (atc:ATC) ON (atc.codigoatc)",
            "CREATE INDEX IF NOT EXISTS FOR (dcp:DCP) ON (dcp.codigodcp)",
            "CREATE INDEX IF NOT EXISTS FOR (dcpf:DCPF) ON (dcpf.codigodcpf)",
            "CREATE INDEX IF NOT EXISTS FOR (dcsa:DCSA) ON (dcsa.codigodcsa)",
            "CREATE INDEX IF NOT EXISTS FOR (envase:Envase) ON (envase.codigoenvase)",
            "CREATE INDEX IF NOT EXISTS FOR (lab:Laboratorio) ON (lab.codigolaboratorio)",
            "CREATE INDEX IF NOT EXISTS FOR (pa:PrincipioActivo) ON (pa.codigoprincipioactivo)",
            "CREATE INDEX IF NOT EXISTS FOR (sr:SituacionRegistro) ON (sr.codigosituacionregistro)",
            "CREATE INDEX IF NOT EXISTS FOR (uc:UnidadContenido) ON (uc.codigounidadcontenido)",
            "CREATE INDEX IF NOT EXISTS FOR (va:ViaAdministracion) ON (va.codigoviaadministracion)",
            "CREATE INDEX IF NOT EXISTS FOR (p:Prescripcion) ON (p.nro_definitivo)",
            "CREATE INDEX IF NOT EXISTS FOR (ffs:FormaFarmaceuticaSimplificada) ON (ffs.codigoformafarmaceuticasimplificada)"
        ]

        for index_query in indexes:
            self.run_query(index_query)

        logger.info("Indexes created successfully")


def main():
    """Main function to execute the Neo4j loading process"""
    try:
        # Initialize Neo4j connection
        loader = Neo4jLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

        # Load all nodes
        logger.info("Starting to load all nodes into Neo4j...")
        loader.load_all_nodes()
        logger.info("Finished loading all nodes into Neo4j")

        # Create all relationships
        logger.info("Starting to create relationships in Neo4j...")
        loader.create_all_relationships()
        logger.info("Finished creating relationships in Neo4j")

        # Close connection
        loader.close()
    except Exception as e:
        logger.error(f"An error occurred during Neo4j loading: {e}")


if __name__ == "__main__":
    main()
