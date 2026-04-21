"""Interactions endpoints."""
import logging
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from src.api.schemas.responses import PaginatedResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_interactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    type: Optional[str] = Query(None, description="Filter by interaction type"),
):
    """Get paginated list of drug interactions with optional filters."""
    from src.api.main import get_mongodb
    try:
        return get_mongodb().get_interactions(page, page_size, severity, type)
    except Exception as e:
        logger.error(f"Failed to list interactions: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.get("/drug/{cod_nacion}")
async def get_interactions_for_drug(cod_nacion: str):
    """Get all interactions for a specific drug."""
    from src.api.main import get_mongodb
    try:
        return get_mongodb().get_interactions_for_drug(cod_nacion)
    except Exception as e:
        logger.error(f"Failed to get interactions for drug {cod_nacion}: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")
