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


@router.get("/severity-type-matrix")
async def get_severity_type_matrix():
    """Cross-tabulation of interaction type x severity (heatmap data)."""
    from src.api.main import get_mongodb
    try:
        return get_mongodb().get_severity_type_matrix()
    except Exception as e:
        logger.error(f"Failed to build severity/type matrix: {e}")
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

    def approach_view(block: dict) -> dict:
        """Compact per-approach view: headline metrics + per-class + confusion."""
        macro = block.get('macro', {}) or {}
        weighted = block.get('weighted', {}) or {}
        per_class = block.get('per_class', {}) or {}
        # per-class as a list sorted by support (desc) for easy rendering
        classes = [
            {
                'label': cls,
                'precision': m.get('precision'),
                'recall': m.get('recall'),
                'f1': m.get('f1'),
                'support': m.get('support'),
            }
            for cls, m in sorted(per_class.items(), key=lambda kv: -kv[1].get('support', 0))
        ]
        return {
            'accuracy': block.get('accuracy'),
            'macro_f1': macro.get('f1'),
            'weighted_f1': weighted.get('f1'),
            'per_class': classes,
            'confusion': block.get('confusion'),
        }

    tasks = []
    for task in ['severity', 'type', 'mechanism']:
        block = results.get(task, {})
        regex = approach_view(block.get('regex', {}))
        spacy = approach_view(block.get('spacy', {}))
        regex_f1 = regex['macro_f1']
        spacy_f1 = spacy['macro_f1']
        # "best" decided on accuracy (the fair headline metric), F1 as tie-break
        best = None
        if regex['accuracy'] is not None and spacy['accuracy'] is not None:
            if regex['accuracy'] != spacy['accuracy']:
                best = 'regex' if regex['accuracy'] > spacy['accuracy'] else 'spacy'
            elif regex_f1 is not None and spacy_f1 is not None:
                best = 'regex' if regex_f1 >= spacy_f1 else 'spacy'
        tasks.append({
            'task': task,
            # backward-compatible macro-F1 fields
            'regex_f1': regex_f1,
            'spacy_f1': spacy_f1,
            'best': best,
            # rich metrics
            'regex': regex,
            'spacy': spacy,
        })

    return {
        'samples': meta.get('ground_truth_samples'),
        'model': meta.get('spacy_model'),
        'gold_source': meta.get('gold_source'),
        'generated_at': meta.get('timestamp'),
        'tasks': tasks,
    }
