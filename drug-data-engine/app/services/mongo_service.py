from bson import ObjectId
from app.core.database import get_mongo_client

COLLECTION_NAME = "diccionario_atc"  # Just for testing


def get_all_items():
    db = get_mongo_client()
    items = list(db[COLLECTION_NAME].find())
    for item in items:
        item["_id"] = str(item["_id"])
    return items


def get_item_by_id(item_id: str):
    db = get_mongo_client()
    item = db[COLLECTION_NAME].find_one({"_id": ObjectId(item_id)})
    if item:
        item["_id"] = str(item["_id"])
    return item


def create_item(data: dict):
    db = get_mongo_client()
    result = db[COLLECTION_NAME].insert_one(data)
    return {"_id": str(result.inserted_id)}


def update_item(item_id: str, update_data: dict):
    db = get_mongo_client()
    result = db[COLLECTION_NAME].update_one(
        {"_id": ObjectId(item_id)}, {"$set": update_data}
    )
    return result.modified_count > 0


def delete_item(item_id: str):
    db = get_mongo_client()
    result = db[COLLECTION_NAME].delete_one({"_id": ObjectId(item_id)})
    return result.deleted_count > 0
