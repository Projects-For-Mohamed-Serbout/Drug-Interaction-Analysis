"""Dashboard endpoints."""
import logging
from fastapi import APIRouter, HTTPException
from src.api.schemas.responses import DashboardStats

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get statistics for the dashboard cards."""
    from src.api.main import get_mongodb
    try:
        return get_mongodb().get_dashboard_stats()
    except Exception as e:
        logger.error(f"Failed to fetch dashboard stats: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")
