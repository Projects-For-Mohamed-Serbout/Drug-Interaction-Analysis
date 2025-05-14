from neo4j import GraphDatabase
from app.core.config import settings

driver = GraphDatabase.driver(
    settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
)


def get_duplicidad_count() -> int:
    query = "MATCH (d:Duplicidad) RETURN count(d) AS count"
    with driver.session() as session:
        result = session.run(query)
        record = result.single()
        return record["count"] if record else 0
