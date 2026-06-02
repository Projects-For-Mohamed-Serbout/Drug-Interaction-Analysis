"""NLP Analysis endpoints."""
import json
import logging
from pathlib import Path
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


@router.get("/evaluation")
async def get_nlp_evaluation():
    """Get the latest NLP evaluation: macro-F1 of regex vs spaCy (RQ1)."""
    results_dir = Path(__file__).parent.parent.parent.parent / 'results'
    files = sorted(results_dir.glob('nlp_evaluation_*.json'), reverse=True)
    if not files:
        raise HTTPException(
            status_code=404,
            detail="No NLP evaluation found. Run scripts/evaluate_nlp.py --output results/ first."
        )

    with open(files[0], encoding='utf-8') as f:
        data = json.load(f)

    meta = data.get('metadata', {})
    results = data.get('results', {})

    tasks = []
    for task in ['severity', 'type', 'mechanism']:
        block = results.get(task, {})
        regex_f1 = (block.get('regex', {}).get('macro', {}) or {}).get('f1')
        spacy_f1 = (block.get('spacy', {}).get('macro', {}) or {}).get('f1')
        best = None
        if regex_f1 is not None and spacy_f1 is not None:
            best = 'regex' if regex_f1 >= spacy_f1 else 'spacy'
        tasks.append({
            'task': task,
            'regex_f1': regex_f1,
            'spacy_f1': spacy_f1,
            'best': best,
        })

    return {
        'samples': meta.get('ground_truth_samples'),
        'model': meta.get('spacy_model'),
        'generated_at': meta.get('timestamp'),
        'tasks': tasks,
    }
