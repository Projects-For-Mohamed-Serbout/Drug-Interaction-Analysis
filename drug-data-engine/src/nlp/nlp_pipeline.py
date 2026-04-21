"""
NLP Pipeline for Drug Interaction Analysis.

Orchestrates the complete NLP processing of drug interactions,
including severity classification, type classification, and
mechanism extraction.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

from .severity_classifier import SeverityClassifier, Severity, SeverityResult
from .interaction_type_classifier import InteractionTypeClassifier, InteractionType, InteractionTypeResult
from .mechanism_extractor import MechanismExtractor, MechanismCategory, MechanismResult

logger = logging.getLogger(__name__)


@dataclass
class NLPAnalysisResult:
    """Complete NLP analysis result for a drug interaction."""
    # Severity
    severity: str
    severity_confidence: float

    # Type
    interaction_type: str
    secondary_types: List[str]
    effect_category: str
    type_confidence: float

    # Mechanism
    mechanism_category: str
    pk_mechanisms: List[str]
    pd_mechanisms: List[str]
    enzymes: List[str]
    transporters: List[str]
    receptors: List[str]
    mechanism_confidence: float

    # Overall
    overall_confidence: float
    processed_at: str
    processing_notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        return asdict(self)

    def to_mongo_update(self) -> Dict[str, Any]:
        """Return MongoDB update format for the nlp subdocument."""
        return {
            'interaccion.nlp.severidad': self.severity,
            'interaccion.nlp.tipo': self.interaction_type,
            'interaccion.nlp.tipos_secundarios': self.secondary_types,
            'interaccion.nlp.categoria_efecto': self.effect_category,
            'interaccion.nlp.mecanismo': self.mechanism_category,
            'interaccion.nlp.mecanismos_pk': self.pk_mechanisms,
            'interaccion.nlp.mecanismos_pd': self.pd_mechanisms,
            'interaccion.nlp.enzimas': self.enzymes,
            'interaccion.nlp.transportadores': self.transporters,
            'interaccion.nlp.receptores': self.receptors,
            'interaccion.nlp.confianza': self.overall_confidence,
            'interaccion.nlp.procesado': True,
            'interaccion.nlp.fecha_procesado': self.processed_at,
            'interaccion.nlp.notas': self.processing_notes,
        }


class NLPPipeline:
    """
    Complete NLP pipeline for drug interaction analysis.

    Combines severity classification, interaction type classification,
    and mechanism extraction into a unified processing pipeline.
    """

    def __init__(self):
        """Initialize the NLP pipeline with all classifiers."""
        logger.info("Initializing NLP Pipeline...")

        self.severity_classifier = SeverityClassifier()
        self.type_classifier = InteractionTypeClassifier()
        self.mechanism_extractor = MechanismExtractor()

        logger.info("NLP Pipeline initialized successfully")

    def analyze(self, effect: str, recommendation: str = "") -> NLPAnalysisResult:
        """
        Perform complete NLP analysis on an interaction.

        Args:
            effect: The effect description (Spanish text)
            recommendation: The recommendation text (Spanish text)

        Returns:
            NLPAnalysisResult with all analysis results
        """
        processing_notes = []

        # Severity classification
        try:
            severity_result = self.severity_classifier.classify(effect, recommendation)
        except Exception as e:
            logger.error(f"Severity classification failed: {e}")
            severity_result = SeverityResult(
                severity=Severity.UNKNOWN,
                confidence=0.0,
                matched_patterns=[],
                reasoning=f"Error: {str(e)}"
            )
            processing_notes.append(f"Severity error: {str(e)}")

        # Type classification
        try:
            type_result = self.type_classifier.classify(effect, recommendation)
        except Exception as e:
            logger.error(f"Type classification failed: {e}")
            type_result = InteractionTypeResult(
                primary_type=InteractionType.OTHER,
                secondary_types=[],
                confidence=0.0,
                matched_patterns={},
                effect_category="Error"
            )
            processing_notes.append(f"Type error: {str(e)}")

        # Mechanism extraction
        try:
            mechanism_result = self.mechanism_extractor.extract(effect, recommendation)
        except Exception as e:
            logger.error(f"Mechanism extraction failed: {e}")
            mechanism_result = MechanismResult(
                category=MechanismCategory.UNKNOWN,
                pk_mechanisms=[],
                pd_mechanisms=[],
                enzymes_involved=[],
                transporters_involved=[],
                receptors_involved=[],
                confidence=0.0,
                extracted_phrases=[]
            )
            processing_notes.append(f"Mechanism error: {str(e)}")

        # Calculate overall confidence
        confidences = [
            severity_result.confidence,
            type_result.confidence,
            mechanism_result.confidence
        ]
        overall_confidence = sum(confidences) / len(confidences)

        # Add reasoning notes
        if severity_result.reasoning:
            processing_notes.append(f"Severity: {severity_result.reasoning}")

        return NLPAnalysisResult(
            # Severity
            severity=severity_result.severity.value,
            severity_confidence=severity_result.confidence,

            # Type
            interaction_type=type_result.primary_type.value,
            secondary_types=[t.value for t in type_result.secondary_types],
            effect_category=type_result.effect_category,
            type_confidence=type_result.confidence,

            # Mechanism
            mechanism_category=mechanism_result.category.value,
            pk_mechanisms=[m.value for m in mechanism_result.pk_mechanisms],
            pd_mechanisms=[m.value for m in mechanism_result.pd_mechanisms],
            enzymes=mechanism_result.enzymes_involved,
            transporters=mechanism_result.transporters_involved,
            receptors=mechanism_result.receptors_involved,
            mechanism_confidence=mechanism_result.confidence,

            # Overall
            overall_confidence=overall_confidence,
            processed_at=datetime.now().isoformat(),
            processing_notes=processing_notes[:5]  # Limit notes
        )

    def analyze_batch(
        self,
        interactions: List[Dict],
        progress_callback: Optional[callable] = None
    ) -> List[NLPAnalysisResult]:
        """
        Analyze multiple interactions.

        Args:
            interactions: List of dicts with 'efecto' and 'recomendacion' keys
            progress_callback: Optional callback(current, total) for progress

        Returns:
            List of NLPAnalysisResult objects
        """
        results = []
        total = len(interactions)

        for i, interaction in enumerate(interactions):
            effect = interaction.get('efecto', interaction.get('effect', ''))
            recommendation = interaction.get('recomendacion', interaction.get('recommendation', ''))

            result = self.analyze(effect, recommendation)
            results.append(result)

            if progress_callback and (i + 1) % 1000 == 0:
                progress_callback(i + 1, total)

        return results

    def get_statistics(self, results: List[NLPAnalysisResult]) -> Dict[str, Any]:
        """
        Calculate statistics from analysis results.

        Args:
            results: List of NLPAnalysisResult objects

        Returns:
            Dictionary with statistics
        """
        if not results:
            return {}

        # Severity distribution
        severity_counts = {}
        for r in results:
            severity_counts[r.severity] = severity_counts.get(r.severity, 0) + 1

        # Type distribution
        type_counts = {}
        for r in results:
            type_counts[r.interaction_type] = type_counts.get(r.interaction_type, 0) + 1

        # Effect category distribution
        category_counts = {}
        for r in results:
            category_counts[r.effect_category] = category_counts.get(r.effect_category, 0) + 1

        # Mechanism distribution
        mechanism_counts = {}
        for r in results:
            mechanism_counts[r.mechanism_category] = mechanism_counts.get(r.mechanism_category, 0) + 1

        # Average confidence
        avg_confidence = sum(r.overall_confidence for r in results) / len(results)

        # High confidence count
        high_confidence = sum(1 for r in results if r.overall_confidence >= 0.7)

        # Enzyme usage
        enzyme_counts = {}
        for r in results:
            for enzyme in r.enzymes:
                enzyme_counts[enzyme] = enzyme_counts.get(enzyme, 0) + 1

        return {
            'total_analyzed': len(results),
            'severity_distribution': severity_counts,
            'type_distribution': type_counts,
            'category_distribution': category_counts,
            'mechanism_distribution': mechanism_counts,
            'average_confidence': round(avg_confidence, 3),
            'high_confidence_count': high_confidence,
            'high_confidence_percentage': round(100 * high_confidence / len(results), 1),
            'top_enzymes': dict(sorted(enzyme_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
        }
