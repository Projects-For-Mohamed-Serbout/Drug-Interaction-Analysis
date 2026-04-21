"""
NLP Pipeline using spaCy and NLTK.

This is the main orchestrator that combines all spaCy-based classifiers
for a complete NLP analysis of drug interactions.
"""

import spacy
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

from .severity_classifier_spacy import SeverityClassifierSpacy, Severity, SeverityResult
from .interaction_type_classifier_spacy import InteractionTypeClassifierSpacy, InteractionType, InteractionTypeResult
from .mechanism_extractor_spacy import MechanismExtractorSpacy, MechanismCategory, MechanismResult

logger = logging.getLogger(__name__)


@dataclass
class NLPAnalysisResult:
    """Complete NLP analysis result for a drug interaction."""
    # Severity
    severity: str
    severity_confidence: float

    # Interaction type
    interaction_type: str
    secondary_types: List[str]
    effect_category: str

    # Mechanism
    mechanism_category: str
    enzymes: List[str]
    transporters: List[str]
    receptors: List[str]

    # Overall
    overall_confidence: float
    processing_notes: List[str]
    processed_at: str

    # Detailed results for comparison
    linguistic_features: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for database storage."""
        return {
            'severidad': self.severity,
            'severidad_confianza': self.severity_confidence,
            'tipo': self.interaction_type,
            'tipos_secundarios': self.secondary_types,
            'categoria_efecto': self.effect_category,
            'mecanismo': self.mechanism_category,
            'enzimas': self.enzymes,
            'transportadores': self.transporters,
            'receptores': self.receptors,
            'confianza_general': self.overall_confidence,
            'notas_procesamiento': self.processing_notes,
            'procesado_en': self.processed_at,
            'caracteristicas_linguisticas': self.linguistic_features,
            'metodo_nlp': 'spacy',  # Mark as spaCy method
        }


class NLPPipelineSpacy:
    """
    Complete NLP pipeline using spaCy and NLTK.

    This pipeline:
    1. Loads a shared spaCy model for all classifiers
    2. Processes text through severity, type, and mechanism analysis
    3. Returns comprehensive NLP analysis results

    Differences from regex approach:
    - Uses lemmatization for better term matching
    - Employs dependency parsing for context
    - Can detect negation and modifiers
    - Uses named entity recognition for pharmacological entities
    - Processes batches more efficiently with spaCy.pipe()
    """

    def __init__(self, model_name: str = "es_core_news_md"):
        """
        Initialize the spaCy NLP pipeline.

        Args:
            model_name: Spanish spaCy model to use
                       - es_core_news_sm: Small (faster, less accurate)
                       - es_core_news_md: Medium (balanced)
                       - es_core_news_lg: Large (slower, more accurate)
        """
        self.model_name = model_name
        logger.info(f"Initializing spaCy NLP Pipeline with model: {model_name}")

        # Initialize classifiers (they share the same model internally)
        self.severity_classifier = SeverityClassifierSpacy(model_name)
        self.type_classifier = InteractionTypeClassifierSpacy(model_name)
        self.mechanism_extractor = MechanismExtractorSpacy(model_name)

        logger.info("spaCy NLP Pipeline initialized successfully")

    def analyze(self, effect: str, recommendation: str = "") -> NLPAnalysisResult:
        """
        Perform complete NLP analysis on an interaction.

        Args:
            effect: Effect description (Spanish text)
            recommendation: Recommendation text (Spanish text)

        Returns:
            NLPAnalysisResult with all classification results
        """
        processing_notes = []
        text = f"{effect} {recommendation}".strip()

        if not text:
            return NLPAnalysisResult(
                severity=Severity.UNKNOWN.value,
                severity_confidence=0.0,
                interaction_type=InteractionType.OTHER.value,
                secondary_types=[],
                effect_category="Unclassified",
                mechanism_category=MechanismCategory.UNKNOWN.value,
                enzymes=[],
                transporters=[],
                receptors=[],
                overall_confidence=0.0,
                processing_notes=["No text provided"],
                processed_at=datetime.now().isoformat(),
            )

        # Classify severity
        try:
            severity_result = self.severity_classifier.classify(effect, recommendation)
            processing_notes.append(f"Severity: {severity_result.reasoning}")
        except Exception as e:
            logger.error(f"Severity classification error: {e}")
            severity_result = SeverityResult(
                severity=Severity.UNKNOWN,
                confidence=0.0,
                matched_terms=[],
                linguistic_features={},
                reasoning=f"Error: {str(e)}"
            )
            processing_notes.append(f"Severity error: {str(e)}")

        # Classify interaction type
        try:
            type_result = self.type_classifier.classify(effect, recommendation)
            processing_notes.append(f"Type: {type_result.effect_category}")
        except Exception as e:
            logger.error(f"Type classification error: {e}")
            type_result = InteractionTypeResult(
                primary_type=InteractionType.OTHER,
                secondary_types=[],
                confidence=0.0,
                matched_terms={},
                effect_category="Unclassified",
                linguistic_analysis={}
            )
            processing_notes.append(f"Type error: {str(e)}")

        # Extract mechanism
        try:
            mechanism_result = self.mechanism_extractor.extract(effect, recommendation)
            processing_notes.append(f"Mechanism: {mechanism_result.reasoning}")
        except Exception as e:
            logger.error(f"Mechanism extraction error: {e}")
            mechanism_result = MechanismResult(
                category=MechanismCategory.UNKNOWN,
                confidence=0.0,
                reasoning=f"Error: {str(e)}"
            )
            processing_notes.append(f"Mechanism error: {str(e)}")

        # Calculate overall confidence
        confidences = [
            severity_result.confidence,
            type_result.confidence,
            mechanism_result.confidence
        ]
        overall_confidence = sum(confidences) / len(confidences)

        # Compile linguistic features for comparison
        linguistic_features = {
            'severity_matched_terms': severity_result.matched_terms,
            'severity_linguistic': severity_result.linguistic_features,
            'type_matched_terms': type_result.matched_terms,
            'type_linguistic': type_result.linguistic_analysis,
            'mechanism_entities': mechanism_result.extracted_entities,
        }

        return NLPAnalysisResult(
            severity=severity_result.severity.value,
            severity_confidence=severity_result.confidence,
            interaction_type=type_result.primary_type.value,
            secondary_types=[t.value for t in type_result.secondary_types],
            effect_category=type_result.effect_category,
            mechanism_category=mechanism_result.category.value,
            enzymes=mechanism_result.enzymes,
            transporters=mechanism_result.transporters,
            receptors=mechanism_result.receptors,
            overall_confidence=overall_confidence,
            processing_notes=processing_notes,
            processed_at=datetime.now().isoformat(),
            linguistic_features=linguistic_features,
        )

    def analyze_batch(self, interactions: List[Dict], batch_size: int = 100) -> List[NLPAnalysisResult]:
        """
        Analyze multiple interactions efficiently.

        Args:
            interactions: List of dicts with 'effect'/'efecto' and 'recommendation'/'recomendacion'
            batch_size: Number of interactions to process in each batch

        Returns:
            List of NLPAnalysisResult objects
        """
        results = []
        total = len(interactions)

        logger.info(f"Processing {total} interactions with spaCy pipeline")

        for i in range(0, total, batch_size):
            batch = interactions[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size

            logger.info(f"Processing batch {batch_num}/{total_batches}")

            # Process each interaction in batch
            for interaction in batch:
                effect = interaction.get('effect', interaction.get('efecto', ''))
                recommendation = interaction.get('recommendation', interaction.get('recomendacion', ''))

                result = self.analyze(effect, recommendation)
                results.append(result)

        logger.info(f"Completed processing {total} interactions")
        return results

    def get_model_info(self) -> Dict:
        """Get information about the loaded spaCy model."""
        nlp = self.severity_classifier.nlp
        return {
            'model_name': self.model_name,
            'pipeline_components': nlp.pipe_names,
            'vocab_size': len(nlp.vocab),
            'has_vectors': nlp.vocab.vectors.shape[0] > 0,
            'vectors_shape': nlp.vocab.vectors.shape if nlp.vocab.vectors.shape[0] > 0 else None,
        }


# Convenience function for quick analysis
def analyze_interaction(effect: str, recommendation: str = "",
                       model_name: str = "es_core_news_md") -> NLPAnalysisResult:
    """
    Quick analysis of a single interaction.

    Args:
        effect: Effect description
        recommendation: Recommendation text
        model_name: spaCy model to use

    Returns:
        NLPAnalysisResult
    """
    pipeline = NLPPipelineSpacy(model_name)
    return pipeline.analyze(effect, recommendation)
