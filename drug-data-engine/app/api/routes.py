from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Dict
from app.schemas.schemas import MedicationSearchResult, MedicationDetail, ActiveIngredient, DuplicityWarning

from app.services.neo4j_service import (
    search_medications,
    get_medication_details,
    get_medication_composition,
    get_medication_duplicities,
    get_duplicidad_count
)

from app.services.mongo_service import (
    get_collection_count,
)


router = APIRouter()

# =======================
# 📦 MongoDB
# =======================


@router.get("/dashboard/stats", tags=["Dashboard"])
def get_dashboard_stats():
    return {
        "medications": get_collection_count("prescriptions"),
        "ingredients": get_collection_count("diccionario_principios_activos"),
        "interactions": get_duplicidad_count(),  # Using Neo4j
    }


# =======================
# 📦 Neo4j
# =======================
@router.get("/medications/search", response_model=List[MedicationSearchResult])
async def search_medications_route(
    q: str = Query(..., description="Search term (medication name, national code or active ingredient)")
):
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search term must be at least 2 characters")

    results = search_medications(q.strip())
    return results


@router.get("/medications/{id}", response_model=MedicationDetail)
async def get_medication_route(
    id: str = Path(..., description="Medication definitive number (nro_definitivo)")
):
    """
    Get detailed information about a specific medication by its definitive number (nro_definitivo).
    """
    medication = get_medication_details(id)
    if not medication:
        raise HTTPException(status_code=404, detail=f"Medication with ID {id} not found")

    return medication


@router.get("/medications/{id}/composition", response_model=List[ActiveIngredient])
async def get_medication_composition_route(
    id: str = Path(..., description="Medication definitive number (nro_definitivo)")
):
    """
    Get composition details (active ingredients) for a specific medication.
    """
    composition = get_medication_composition(id)
    if not composition:
        raise HTTPException(status_code=404, detail=f"Composition for medication with ID {id} not found")

    return composition


@router.get("/medications/{id}/duplicities", response_model=List[DuplicityWarning])
async def get_medication_duplicities_route(
    id: str = Path(..., description="Medication definitive number (nro_definitivo)")
):
    """
    Get duplicity warnings for a specific medication.

    This endpoint returns information about potential drug interactions or duplications
    between this medication and others based on their ATC codes. It includes details
    about the effect of the interaction and recommendations for healthcare providers.
    """
    duplicities = get_medication_duplicities(id)
    return duplicities


@router.get("/stats/duplicities", response_model=Dict[str, int])
async def get_duplicities_count_route():
    """
    Get count of duplicities in the database.
    """
    count = get_duplicidad_count()
    return {"count": count}
