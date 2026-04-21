"""Medications endpoints."""
import logging
from typing import List
from fastapi import APIRouter, Query, HTTPException
from src.api.schemas.responses import Medication, PaginatedResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search", response_model=List[Medication])
async def search_medications(q: str = Query(..., min_length=1, description="Search query")):
    """Search medications by name, code, or active ingredient."""
    from src.api.main import get_mongodb
    try:
        return get_mongodb().search_medications(q)
    except Exception as e:
        logger.error(f"Failed to search medications: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.get("", response_model=PaginatedResponse)
async def list_medications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query('nombre_comercial'),
    sort_order: str = Query('asc', pattern='^(asc|desc)$'),
):
    """Get paginated list of all medications."""
    from src.api.main import get_mongodb
    try:
        return get_mongodb().get_medications(page, page_size, sort_by, sort_order)
    except Exception as e:
        logger.error(f"Failed to list medications: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.get("/{cod_nacion}")
async def get_medication(cod_nacion: str):
    """Get a single medication by its national code."""
    from src.api.main import get_mongodb
    try:
        result = get_mongodb().get_medication_by_id(cod_nacion)
    except Exception as e:
        logger.error(f"Failed to get medication {cod_nacion}: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")
    if not result:
        raise HTTPException(status_code=404, detail="Medication not found")
    return result
