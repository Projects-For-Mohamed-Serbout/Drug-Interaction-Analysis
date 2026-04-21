"""
NLP Module using spaCy and NLTK.

This is a separate implementation from the pattern-based approach
to compare effectiveness of different NLP techniques for
Spanish pharmaceutical text classification.
"""

from .severity_classifier_spacy import SeverityClassifierSpacy, Severity, SeverityResult
from .interaction_type_classifier_spacy import InteractionTypeClassifierSpacy, InteractionType, InteractionTypeResult
from .mechanism_extractor_spacy import MechanismExtractorSpacy, MechanismCategory, MechanismResult
from .nlp_pipeline_spacy import NLPPipelineSpacy, NLPAnalysisResult

__all__ = [
    'SeverityClassifierSpacy',
    'Severity',
    'SeverityResult',
    'InteractionTypeClassifierSpacy',
    'InteractionType',
    'InteractionTypeResult',
    'MechanismExtractorSpacy',
    'MechanismCategory',
    'MechanismResult',
    'NLPPipelineSpacy',
    'NLPAnalysisResult',
]
