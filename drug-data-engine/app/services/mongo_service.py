from bson import ObjectId
from app.core.database import get_mongo_client
from bson import errors as bson_errors


def get_all_items(collection_name: str):
    db = get_mongo_client()
    items = list(db[collection_name].find())
    for item in items:
        item["_id"] = str(item["_id"])
    return items


def get_item_by_id(collection_name: str, item_id: str):
    db = get_mongo_client()
    try:
        item = db[collection_name].find_one({"_id": ObjectId(item_id)})
    except bson_errors.InvalidId:
        return None
    if item:
        item["_id"] = str(item["_id"])
    return item


def create_item(collection_name: str, data: dict):
    db = get_mongo_client()
    result = db[collection_name].insert_one(data)
    return {"_id": str(result.inserted_id)}


def update_item(collection_name: str, item_id: str, update_data: dict):
    db = get_mongo_client()
    result = db[collection_name].update_one(
        {"_id": ObjectId(item_id)}, {"$set": update_data}
    )
    return result.modified_count > 0


def delete_item(collection_name: str, item_id: str):
    db = get_mongo_client()
    result = db[collection_name].delete_one({"_id": ObjectId(item_id)})
    return result.deleted_count > 0
