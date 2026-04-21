"""
Pydantic response models for the API.
"""
from typing import List, Optional, Any
from pydantic import BaseModel


# =========================================================================
# Dashboard
# =========================================================================
class DashboardStats(BaseModel):
    medications: int
    ingredients: int
    interactions: int
    laboratories: int
    atc_codes: int


# =========================================================================
# Medications
# =========================================================================
class Medication(BaseModel):
    id: str
    codigo_nacional: str
    nombre: str
    principio_activo: str
    laboratorio: str
    via_administracion: str
    matched_by: str = 'name'


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# =========================================================================
# NLP Analysis
# =========================================================================
class DistributionItem(BaseModel):
    label: str
    count: int


class NLPStatistics(BaseModel):
    total_interactions: int
    processed: int
    unprocessed: int
    processing_rate: float
    severity_distribution: List[DistributionItem]
    type_distribution: List[DistributionItem]
    effect_category_distribution: List[DistributionItem]
    mechanism_distribution: List[DistributionItem]
    average_confidence: float


# =========================================================================
# Database Performance
# =========================================================================
class BenchmarkQuery(BaseModel):
    query: str
    description: Optional[str] = None
    category: Optional[str] = None
    mongodb_ms: Optional[float] = None
    neo4j_ms: Optional[float] = None
    mongodb_p95_ms: Optional[float] = None
    neo4j_p95_ms: Optional[float] = None
    winner: str
    speedup: Optional[str] = None
    row_count_match: Optional[bool] = None


class CategoryBreakdown(BaseModel):
    category: str
    mongodb_wins: int
    neo4j_wins: int
    comparable: int


class BenchmarkSummary(BaseModel):
    queries: List[BenchmarkQuery]
    mongodb_wins: int
    neo4j_wins: int
    comparable_count: int
    mongodb_avg_ms: float
    neo4j_avg_ms: float
    overall_winner: str
    speedup_factor: float
    graph_exclusive_queries: int
    category_breakdown: List[CategoryBreakdown]
    iterations: Optional[int] = None
    row_count_mismatches: int = 0
