"""
Tests for FastAPI endpoints.
Uses TestClient to validate API responses.
Requires database connections — tests are skipped if DB is unavailable.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from src.api.main import app, get_mongodb

client = TestClient(app)

# Check if DB is available (lifespan connected)
def db_available():
    try:
        return get_mongodb() is not None
    except Exception:
        return False

pytestmark = pytest.mark.skipif(
    not db_available(),
    reason="Database not connected (API tests require running MongoDB)"
)


class TestHealthEndpoint:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "mongodb" in data
        assert "neo4j" in data


class TestDashboardEndpoint:
    def test_get_stats(self):
        response = client.get("/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert "medications" in data
        assert "ingredients" in data
        assert "interactions" in data
        assert data["medications"] > 0


class TestMedicationsEndpoints:
    def test_search(self):
        response = client.get("/medications/search?q=IBUPROFENO")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "nombre" in data[0]
            assert "codigo_nacional" in data[0]

    def test_search_min_length(self):
        response = client.get("/medications/search?q=")
        assert response.status_code == 422  # Validation error

    def test_list_paginated(self):
        response = client.get("/medications?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "total_pages" in data
        assert len(data["items"]) <= 5

    def test_get_by_id(self):
        response = client.get("/medications/600023")
        assert response.status_code == 200
        data = response.json()
        assert data["cod_nacion"] == "600023"

    def test_get_not_found(self):
        response = client.get("/medications/999999999")
        assert response.status_code == 404


class TestInteractionsEndpoints:
    def test_list(self):
        response = client.get("/interactions?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_filter_by_severity(self):
        response = client.get("/interactions?severity=contraindicated&page_size=3")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0

    def test_drug_interactions(self):
        response = client.get("/interactions/drug/600023")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestActiveIngredientsEndpoint:
    def test_list(self):
        response = client.get("/active-ingredients?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_search(self):
        response = client.get("/active-ingredients?search=PARACETAMOL")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


class TestLaboratoriesEndpoint:
    def test_list(self):
        response = client.get("/laboratories?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_search(self):
        response = client.get("/laboratories?search=PFIZER")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


class TestNlpAnalysisEndpoint:
    def test_get_statistics(self):
        response = client.get("/nlp-analysis")
        assert response.status_code == 200
        data = response.json()
        assert "total_interactions" in data
        assert "severity_distribution" in data
        assert "type_distribution" in data
        assert "average_confidence" in data
        assert data["total_interactions"] > 0


class TestBenchmarkEndpoint:
    def test_get_results(self):
        response = client.get("/database-performance")
        assert response.status_code == 200
        data = response.json()
        assert "queries" in data
        assert "mongodb_wins" in data
        assert "neo4j_wins" in data
        assert len(data["queries"]) > 0
