from fastapi import APIRouter, HTTPException
from app.services.mongo_service import (
    create_item,
    get_all_items,
    get_item_by_id,
    update_item,
    delete_item,
    get_collection_count,
)
from app.services.neo4j_service import get_duplicidad_count


router = APIRouter()


# =======================
# 📦 MongoDB: Medications
# =======================
@router.get("/medications/{collection}", tags=["Mongo Collections"])
def read_all_documents(collection: str):
    return get_all_items(collection)


@router.get("/medications/{collection}/{item_id}", tags=["Mongo Collections"])
def read_document(collection: str, item_id: str):
    doc = get_item_by_id(collection, item_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/medications/{collection}", tags=["Mongo Collections"])
def create_document(collection: str, item: dict):
    return create_item(collection, item)


@router.put("/medications/{collection}/{item_id}", tags=["Mongo Collections"])
def update_document(collection: str, item_id: str, update_data: dict):
    updated = update_item(collection, item_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Document not found or not updated")
    return {"message": "Document updated successfully"}


@router.delete("/medications/{collection}/{item_id}", tags=["Mongo Collections"])
def delete_document(collection: str, item_id: str):
    deleted = delete_item(collection, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}


@router.get("/dashboard/stats", tags=["Dashboard"])
def get_dashboard_stats():
    return {
        "medications": get_collection_count("prescriptions"),
        "ingredients": get_collection_count("diccionario_principios_activos"),
        "interactions": get_duplicidad_count(),
    }
