"""NLP Analysis endpoints."""
import logging
from fastapi import APIRouter, HTTPException
from src.api.schemas.responses import NLPStatistics

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=NLPStatistics)
async def get_nlp_statistics():
    """Get NLP processing statistics and distributions."""
    from src.api.main import get_mongodb
    try:
        return get_mongodb().get_nlp_statistics()
    except Exception as e:
        logger.error(f"Failed to fetch NLP statistics: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")
