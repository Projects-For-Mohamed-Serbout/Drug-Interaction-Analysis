"""Dashboard endpoints."""
import json
import logging
from pathlib import Path
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


@router.get("/integrity")
async def get_integrity_report():
    """Get the latest ETL data-integrity verification report."""
    results_dir = Path(__file__).parent.parent.parent.parent / 'results'
    files = sorted(results_dir.glob('integrity_report_*.json'), reverse=True)
    if not files:
        raise HTTPException(
            status_code=404,
            detail="No integrity report found. Run verify_data_integrity.py first."
        )

    with open(files[0], encoding='utf-8') as f:
        data = json.load(f)

    xml = data.get('xml') or {}
    neo4j = data.get('neo4j') or {}
    headline = {
        'drugs': xml.get('drugs'),
        'interactions_raw': xml.get('interactions_raw'),
        'interactions_neo4j': (neo4j.get('relationships') or {}).get('INTERACTS_WITH_ATC'),
        'reference_dictionaries': len(xml.get('reference') or {}),
    }

    return {
        'generated_at': data.get('generated_at'),
        'summary': data.get('summary', {}),
        'checks': data.get('checks', []),
        'headline': headline,
    }
