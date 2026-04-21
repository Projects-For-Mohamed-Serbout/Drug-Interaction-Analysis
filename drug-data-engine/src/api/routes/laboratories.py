"""Laboratories endpoints."""
import logging
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from src.api.schemas.responses import PaginatedResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_laboratories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name"),
):
    """Get paginated list of laboratories."""
    from src.api.main import get_mongodb
    try:
        return get_mongodb().get_laboratories(page, page_size, search)
    except Exception as e:
        logger.error(f"Failed to list laboratories: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")
