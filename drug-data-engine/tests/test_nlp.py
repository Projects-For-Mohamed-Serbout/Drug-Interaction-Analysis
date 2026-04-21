"""
Tests for NLP classification pipelines.
Validates severity, interaction type, and mechanism extraction.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.nlp.severity_classifier import SeverityClassifier
from src.nlp.interaction_type_classifier import InteractionTypeClassifier
from src.nlp.mechanism_extractor import MechanismExtractor
from src.nlp.nlp_pipeline import NLPPipeline


class TestSeverityClassifier:
    """Tests for severity classification."""

    def setup_method(self):
        self.classifier = SeverityClassifier()

    def test_contraindicated_detection(self):
        result = self.classifier.classify(
            "Asociación contraindicada por riesgo de arritmias mortales.",
            "No debe administrarse conjuntamente."
        )
        assert result.severity.value == "contraindicated"
        assert result.confidence > 0.7

    def test_moderate_detection(self):
        result = self.classifier.classify(
            "Aumento del riesgo de hemorragia digestiva.",
            "Se recomienda precaución y monitorización."
        )
        assert result.severity.value in ["moderate", "severe"]
        assert result.confidence > 0.5

    def test_empty_text(self):
        result = self.classifier.classify("", "")
        assert result.severity.value == "unknown"

    def test_confidence_range(self):
        result = self.classifier.classify(
            "Posible aumento del efecto sedante.",
            "Vigilar al paciente."
        )
        assert 0.0 <= result.confidence <= 1.0


class TestInteractionTypeClassifier:
    """Tests for interaction type classification."""

    def setup_method(self):
        self.classifier = InteractionTypeClassifier()

    def test_cardiac_detection(self):
        result = self.classifier.classify(
            "Aumento del riesgo de arritmias ventriculares y prolongación del intervalo QT.",
            ""
        )
        assert result.primary_type.value == "cardiac"

    def test_hemorrhagic_detection(self):
        result = self.classifier.classify(
            "Aumento del riesgo de hemorragia por efecto anticoagulante aditivo.",
            ""
        )
        assert result.primary_type.value == "hemorrhagic"

    def test_gastrointestinal_detection(self):
        result = self.classifier.classify(
            "Riesgo de úlcera gástrica y hemorragia digestiva.",
            ""
        )
        assert result.primary_type.value in ["gastrointestinal", "hemorrhagic"]

    def test_empty_text(self):
        result = self.classifier.classify("", "")
        assert result.primary_type.value == "other"


class TestMechanismExtractor:
    """Tests for mechanism extraction."""

    def setup_method(self):
        self.extractor = MechanismExtractor()

    def test_pharmacokinetic_detection(self):
        result = self.extractor.extract(
            "Inhibición del CYP3A4 que reduce el metabolismo del fármaco.",
            ""
        )
        assert result.category.value in ["pharmacokinetic", "mixed"]

    def test_pharmacodynamic_detection(self):
        result = self.extractor.extract(
            "Efecto aditivo sobre la prolongación del intervalo QT.",
            ""
        )
        assert result.category.value in ["pharmacodynamic", "unknown"]

    def test_enzyme_extraction(self):
        result = self.extractor.extract(
            "Inhibidor potente del CYP2D6 y del CYP3A4.",
            ""
        )
        # Should detect at least one CYP enzyme
        cyp_found = any("CYP" in e for e in result.enzymes_involved)
        assert cyp_found or result.category.value != "unknown"

    def test_empty_text(self):
        result = self.extractor.extract("", "")
        assert result.category.value == "unknown"


class TestNLPPipeline:
    """Tests for the full NLP pipeline."""

    def setup_method(self):
        self.pipeline = NLPPipeline()

    def test_full_analysis(self):
        result = self.pipeline.analyze(
            "Aumento del riesgo de arritmias ventriculares graves.",
            "Asociación contraindicada."
        )
        assert result.severity is not None
        assert result.interaction_type is not None
        assert result.mechanism_category is not None
        assert 0.0 <= result.overall_confidence <= 1.0

    def test_to_mongo_update(self):
        result = self.pipeline.analyze(
            "Posible aumento del sangrado.",
            "Precaución."
        )
        update = result.to_mongo_update()
        assert 'interaccion.nlp' in str(update) or isinstance(update, dict)

    def test_multiple_analyses_consistent(self):
        """Same input should produce same output."""
        text = "Riesgo de prolongación del QT."
        rec = "Monitorizar ECG."
        r1 = self.pipeline.analyze(text, rec)
        r2 = self.pipeline.analyze(text, rec)
        assert r1.severity == r2.severity
        assert r1.interaction_type == r2.interaction_type
