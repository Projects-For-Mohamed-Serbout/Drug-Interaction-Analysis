from fastapi import APIRouter, HTTPException
from app.services.mongo_service import (
    create_item,
    get_all_items,
    get_item_by_id,
    update_item,
    delete_item
)

router = APIRouter()


# =======================
# 📦 MongoDB: Medications
# =======================

@router.get("/medications", tags=["Medications"])
def read_all_medications():
    return get_all_items()


@router.get("/medications/{med_id}", tags=["Medications"])
def read_medication(med_id: str):
    med = get_item_by_id(med_id)
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    return med


@router.post("/medications", tags=["Medications"])
def create_medication(item: dict):
    return create_item(item)


@router.put("/medications/{med_id}", tags=["Medications"])
def update_medication(med_id: str, update_data: dict):
    updated = update_item(med_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Medication not found or not updated")
    return {"message": "Medication updated successfully"}


@router.delete("/medications/{med_id}", tags=["Medications"])
def delete_medication(med_id: str):
    success = delete_item(med_id)
    if not success:
        raise HTTPException(status_code=404, detail="Medication not found")
    return {"message": "Medication deleted successfully"}


# =======================
# 📦 Neo4j: Interactions
# =======================
