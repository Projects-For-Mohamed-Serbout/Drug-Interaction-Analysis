from app.core.database import neo4j_driver


def get_neo4j_sample():
    query = "MATCH (n) RETURN n LIMIT 5"

    with neo4j_driver.session() as session:
        result = session.run(query)
        return [record["n"] for record in result]
