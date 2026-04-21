"""
Tests for data extraction modules.
Validates XML parsing and data model creation.
"""
import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.drug import (
    Drug, ActiveIngredient, Laboratory, ATCCode,
    DrugInteraction, PharmaceuticalForm
)
from src.config.settings import get_settings


class TestDataModels:
    """Tests for data model classes."""

    def test_active_ingredient_creation(self):
        ai = ActiveIngredient(codigo=350, codigo_aemps="12A", nombre="PARACETAMOL")
        assert ai.codigo == 350
        assert ai.nombre == "PARACETAMOL"
        d = ai.to_dict()
        assert d['codigo'] == 350
        assert d['nombre'] == "PARACETAMOL"

    def test_laboratory_creation(self):
        lab = Laboratory(codigo=1234, nombre="TEST LAB S.A.")
        assert lab.nombre == "TEST LAB S.A."
        d = lab.to_dict()
        assert 'codigo' in d
        assert 'nombre' in d

    def test_atc_code_creation(self):
        atc = ATCCode(nro=1, codigo="N06AB04", descripcion="citalopram")
        assert atc.codigo == "N06AB04"
        d = atc.to_dict()
        assert d['codigo'] == "N06AB04"

    def test_drug_interaction_creation(self):
        interaction = DrugInteraction(
            atc_interaccion="A03FA03",
            descripcion="domperidona",
            efecto="Aumento del riesgo de arritmias.",
            recomendacion="Contraindicada."
        )
        assert interaction.efecto == "Aumento del riesgo de arritmias."
        d = interaction.to_dict()
        assert 'efecto' in d
        assert 'recomendacion' in d


class TestSettings:
    """Tests for configuration settings."""

    def test_settings_loads(self):
        settings = get_settings()
        assert settings.mongodb_uri != ''
        assert settings.neo4j_uri != ''

    def test_xml_files_defined(self):
        settings = get_settings()
        xml_files = settings.xml_files
        assert 'prescripcion' in xml_files
        assert 'principios_activos' in xml_files
        assert 'laboratorios' in xml_files
        assert len(xml_files) >= 13


class TestExtractors:
    """Tests for XML extractors (requires data files)."""

    def test_dictionary_extractor_import(self):
        from src.extractors.dictionary_extractor import DictionaryExtractor
        assert DictionaryExtractor is not None

    def test_prescription_extractor_import(self):
        from src.extractors.prescription_extractor import PrescriptionExtractor
        assert PrescriptionExtractor is not None

    def test_xml_extractor_import(self):
        from src.extractors.xml_extractor import XMLExtractor
        assert XMLExtractor is not None
