from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from neo4j import GraphDatabase, basic_auth
from neo4j.exceptions import ServiceUnavailable
from app.core.config import settings

mongo_client = None
mongodb = None
neo4j_driver = None


# --- MongoDB ---
def get_mongo_client():
    global mongo_client, mongodb
    if mongo_client is None:
        try:
            mongo_client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
            mongo_client.admin.command("ping")  # check connection
            mongodb = mongo_client[settings.mongodb_db]
            print("✅ MongoDB connected.")
        except ConnectionFailure as e:
            print("❌ MongoDB connection failed:", e)
            mongo_client = None
    return mongodb


# --- Neo4j ---
def get_neo4j_driver():
    global neo4j_driver
    if neo4j_driver is None:
        try:
            neo4j_driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=basic_auth(settings.neo4j_user, settings.neo4j_password)
            )
            with neo4j_driver.session() as session:
                session.run("RETURN 1")  # test connection
            print("✅ Neo4j connected.")
        except ServiceUnavailable as e:
            print("❌ Neo4j connection failed:", e)
            neo4j_driver = None
    return neo4j_driver
