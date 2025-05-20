from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
from app.core.config import settings

driver = GraphDatabase.driver(
    settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
)


def get_duplicidad_count() -> int:
    """Get count of Duplicidad nodes in the database"""
    query = "MATCH (d:Duplicidad) RETURN count(d) AS count"
    with driver.session() as session:
        result = session.run(query)
        record = result.single()
        return record["count"] if record else 0


def search_medications(search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search medications by name, national code, or active ingredient

    Args:
        search_term: Term to search for in medication names, codes, or ingredients
        limit: Maximum number of results to return

    Returns:
        List of medication dictionaries with basic information
    """
    # Create a case-insensitive search pattern
    search_pattern = f"(?i).*{search_term}.*"

    query = """
    // Search by medication name
    MATCH (p:Prescripcion)
    WHERE p.des_nomco =~ $search_pattern

    // Get laboratory information
    OPTIONAL MATCH (p)-[:MANUFACTURED_BY]->(lab:Laboratorio)

    // Get active substance information
    OPTIONAL MATCH (p)-[:CONTAINS_SUBSTANCE]->(dcsa:DCSA)

    // Get administration route
    OPTIONAL MATCH (p)-[:HAS_ADMIN_ROUTE]->(via:ViaAdministracion)

    RETURN p.nro_definitivo AS id,
           p.cod_nacion AS codigo_nacional,
           p.des_nomco AS nombre,
           dcsa.nombredcsa AS principio_activo,
           lab.laboratorio AS laboratorio,
           via.viaadministracion AS via_administracion,
           'nombre' AS matched_by

    UNION

    // Search by national code
    MATCH (p:Prescripcion)
    WHERE p.cod_nacion =~ $search_pattern

    // Get laboratory information
    OPTIONAL MATCH (p)-[:MANUFACTURED_BY]->(lab:Laboratorio)

    // Get active substance information
    OPTIONAL MATCH (p)-[:CONTAINS_SUBSTANCE]->(dcsa:DCSA)

    // Get administration route
    OPTIONAL MATCH (p)-[:HAS_ADMIN_ROUTE]->(via:ViaAdministracion)

    RETURN p.nro_definitivo AS id,
           p.cod_nacion AS codigo_nacional,
           p.des_nomco AS nombre,
           dcsa.nombredcsa AS principio_activo,
           lab.laboratorio AS laboratorio,
           via.viaadministracion AS via_administracion,
           'codigo' AS matched_by

    UNION

    // Search by active ingredient
    MATCH (comp:Composicion)-[:PART_OF]->(p:Prescripcion),
          (comp)-[:USES_INGREDIENT]->(pa:PrincipioActivo)
    WHERE pa.principioactivo =~ $search_pattern

    // Get laboratory information
    OPTIONAL MATCH (p)-[:MANUFACTURED_BY]->(lab:Laboratorio)

    // Get active substance information
    OPTIONAL MATCH (p)-[:CONTAINS_SUBSTANCE]->(dcsa:DCSA)

    // Get administration route
    OPTIONAL MATCH (p)-[:HAS_ADMIN_ROUTE]->(via:ViaAdministracion)

    RETURN p.nro_definitivo AS id,
           p.cod_nacion AS codigo_nacional,
           p.des_nomco AS nombre,
           dcsa.nombredcsa AS principio_activo,
           lab.laboratorio AS laboratorio,
           via.viaadministracion AS via_administracion,
           'principio_activo' AS matched_by

    """

    with driver.session() as session:
        result = session.run(query, search_pattern=search_pattern)
        return [dict(record) for record in result]


def get_medication_details(id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific medication by its definitive number

    Args:
        id: The medication's definitive number (nro_definitivo)

    Returns:
        Dictionary with detailed medication information or None if not found
    """
    query = """
    MATCH (p:Prescripcion)
    WHERE p.nro_definitivo = $id

    // Get laboratory information
    OPTIONAL MATCH (p)-[:MANUFACTURED_BY]->(lab:Laboratorio)

    // Get active substances
    OPTIONAL MATCH (p)-[:CONTAINS_SUBSTANCE]->(dcsa:DCSA)

    // Get administration route
    OPTIONAL MATCH (p)-[:HAS_ADMIN_ROUTE]->(via:ViaAdministracion)

    // Get container information
    OPTIONAL MATCH (p)-[:HAS_CONTAINER]->(env:Envase)

    // Get registration status
    OPTIONAL MATCH (p)-[:HAS_STATUS]->(sit:SituacionRegistro)

    RETURN p.nro_definitivo AS id,
           p.cod_nacion AS codigo_nacional,
           p.des_nomco AS nombre,
           p.contenido AS contenido,
           p.fecha_autorizacion AS fecha_autorizacion,
           p.sw_generico AS es_generico,
           p.url_fictec AS ficha_tecnica_url,

           lab.laboratorio AS laboratorio,
           dcsa.nombredcsa AS sustancia_activa,
           via.viaadministracion AS via_administracion,
           env.envase AS envase,
           sit.situacionregistro AS situacion_registro
    """

    with driver.session() as session:
        result = session.run(query, id=id)
        record = result.single()
        return dict(record) if record else None


def get_medication_composition(id: str) -> List[Dict[str, Any]]:
    """
    Get composition details for a specific medication

    Args:
        id: The medication's definitive number (nro_definitivo)

    Returns:
        List of active ingredients with their dosage information
    """
    query = """
    MATCH (comp:Composicion)-[:PART_OF]->(p:Prescripcion),
          (comp)-[:USES_INGREDIENT]->(pa:PrincipioActivo)
    WHERE p.nro_definitivo = $id

    RETURN pa.principioactivo AS nombre_principio_activo,
           comp.dosis_pa AS dosis,
           comp.unidad_dosis_pa AS unidad_dosis,
           comp.orden_colacion AS orden
    ORDER BY comp.orden_colacion
    """

    with driver.session() as session:
        result = session.run(query, id=id)
        return [dict(record) for record in result]


def get_medication_duplicities(id: str) -> List[Dict[str, Any]]:
    """
    Get duplicity warnings for a specific medication

    Args:
        id: The medication's definitive number (nro_definitivo)

    Returns:
        List of duplicity warnings with their effects and recommendations
    """
    query = """
    MATCH (dup:Duplicidad)-[:RELATES_TO]->(p:Prescripcion),
          (dup)-[:REFERENCES_CODE]->(atc1:ATC),
          (dup)-[:DUPLICATES_CODE]->(atc2:ATC)
    WHERE p.nro_definitivo = $id

    RETURN atc1.descatc AS atc_code_description,
           atc2.descatc AS duplicated_atc_description,
           dup.descripcion AS descripcion,
           dup.efecto AS efecto,
           dup.recomendacion AS recomendacion
    """

    with driver.session() as session:
        result = session.run(query, id=id)
        return [dict(record) for record in result]
