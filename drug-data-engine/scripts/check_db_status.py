"""
Check Database Status - Verify NLP sync and indexes.
"""
from pymongo import MongoClient
from neo4j import GraphDatabase
from src.config import get_settings

def main():
    settings = get_settings()

    print("=" * 70)
    print("DATABASE STATUS CHECK")
    print("=" * 70)

    # ========== MONGODB CHECK ==========
    print("\n[MONGODB STATUS]")
    print("-" * 70)

    mongo_client = MongoClient(settings.mongodb_uri)
    db = mongo_client[settings.mongodb_db]

    # Check collections
    collections = db.list_collection_names()
    print(f"Collections: {collections}")

    # Check drug_interactions collection
    interactions_col = db['drug_interactions']
    total_interactions = interactions_col.count_documents({})
    print(f"\nTotal interactions: {total_interactions}")

    # Check NLP fields in MongoDB
    with_nlp = interactions_col.count_documents({'interaccion.nlp': {'$exists': True}})
    with_severity = interactions_col.count_documents({'interaccion.nlp.severidad': {'$exists': True}})
    with_type = interactions_col.count_documents({'interaccion.nlp.tipo': {'$exists': True}})
    with_mechanism = interactions_col.count_documents({'interaccion.nlp.mecanismo': {'$exists': True}})

    print(f"\nMongoDB NLP Enrichment:")
    print(f"  - With NLP data: {with_nlp}")
    print(f"  - With severity: {with_severity}")
    print(f"  - With type: {with_type}")
    print(f"  - With mechanism: {with_mechanism}")

    # Sample NLP data
    sample = interactions_col.find_one({'interaccion.nlp': {'$exists': True}})
    if sample:
        print(f"\nSample NLP data from MongoDB:")
        nlp = sample.get('interaccion', {}).get('nlp', {})
        print(f"  Severity: {nlp.get('severidad')}")
        print(f"  Type: {nlp.get('tipo')}")
        print(f"  Mechanism: {nlp.get('mecanismo', 'N/A')[:100]}...")

    # Check MongoDB indexes
    print(f"\nMongoDB Indexes on drug_interactions:")
    for idx in interactions_col.list_indexes():
        print(f"  - {idx['name']}")

    mongo_client.close()

    # ========== NEO4J CHECK ==========
    print("\n" + "=" * 70)
    print("[NEO4J STATUS]")
    print("-" * 70)

    neo4j_driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password)
    )

    with neo4j_driver.session() as session:
        # Count nodes
        result = session.run("MATCH (d:Drug) RETURN count(d) as count")
        drug_count = result.single()['count']
        print(f"Drug nodes: {drug_count}")

        result = session.run("MATCH (a:ATCCode) RETURN count(a) as count")
        atc_count = result.single()['count']
        print(f"ATC Code nodes: {atc_count}")

        # Count relationships
        result = session.run("MATCH ()-[r:INTERACTS_WITH_ATC]->() RETURN count(r) as count")
        interaction_count = result.single()['count']
        print(f"INTERACTS_WITH_ATC relationships: {interaction_count}")

        # Check NLP fields on relationships
        result = session.run("""
            MATCH ()-[i:INTERACTS_WITH_ATC]->()
            RETURN
                count(*) AS total,
                count(i.severidad) AS with_severidad,
                count(i.tipo) AS with_tipo,
                count(i.mecanismo) AS with_mecanismo
        """)
        record = result.single()

        print(f"\nNeo4J NLP Sync Status:")
        print(f"  - Total relationships: {record['total']}")
        print(f"  - With severity: {record['with_severidad']}")
        print(f"  - With type: {record['with_tipo']}")
        print(f"  - With mechanism: {record['with_mecanismo']}")

        if record['total'] > 0:
            coverage = (record['with_severidad'] / record['total']) * 100
            print(f"  - Coverage: {coverage:.1f}%")

        # Sample relationship with NLP data
        result = session.run("""
            MATCH (d1:Drug)-[i:INTERACTS_WITH_ATC]->(d2:Drug)
            WHERE i.severidad IS NOT NULL
            RETURN d1.nombre_comercial as drug1, d2.nombre_comercial as drug2,
                   i.severidad as severity, i.tipo as type
            LIMIT 1
        """)
        sample = result.single()
        if sample:
            print(f"\nSample Neo4J relationship with NLP:")
            print(f"  {sample['drug1']} -> {sample['drug2']}")
            print(f"  Severity: {sample['severity']}, Type: {sample['type']}")
        else:
            print(f"\nNo relationships with NLP data found in Neo4J!")

        # Check Neo4J indexes
        print(f"\nNeo4J Indexes:")
        result = session.run("SHOW INDEXES")
        for record in result:
            state = record.get('state', 'unknown')
            name = record.get('name', 'unknown')
            entity = record.get('entityType', '')
            print(f"  - {name} ({entity}) - {state}")

    neo4j_driver.close()

    print("\n" + "=" * 70)
    print("STATUS CHECK COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    main()
