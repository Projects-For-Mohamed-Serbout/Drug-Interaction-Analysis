"""
Base Benchmark Class for Database Performance Testing.

Provides common functionality for timing queries, collecting metrics,
statistical analysis, and environment metadata.
"""
import time
import math
import platform
import statistics
import sys
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# =========================================================================
# Query categories for structured analysis
# =========================================================================
class QueryCategory:
    """Categories for benchmark queries."""
    POINT_LOOKUP = "Point Lookup"
    RANGE_SCAN = "Range Scan"
    TEXT_SEARCH = "Text Search"
    AGGREGATION = "Aggregation"
    RELATIONSHIP_TRAVERSAL = "Relationship Traversal"
    MULTI_HOP_TRAVERSAL = "Multi-hop Traversal"
    PATTERN_MATCHING = "Pattern Matching"
    COMPLEX_FILTER = "Complex Filter"


# =========================================================================
# Data classes
# =========================================================================
@dataclass
class QueryResult:
    """Result of a single query execution."""
    query_name: str
    execution_time_ms: float
    row_count: int
    success: bool
    error_message: Optional[str] = None


@dataclass
class BenchmarkResult:
    """Aggregated benchmark results for a query with full statistical analysis."""
    query_name: str
    query_description: str
    database: str
    category: str
    iterations: int
    warmup_iterations: int = 0
    times_ms: List[float] = field(default_factory=list)
    row_counts: List[int] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # --- Core statistics ---

    @property
    def min_time(self) -> float:
        return min(self.times_ms) if self.times_ms else 0

    @property
    def max_time(self) -> float:
        return max(self.times_ms) if self.times_ms else 0

    @property
    def avg_time(self) -> float:
        return statistics.mean(self.times_ms) if self.times_ms else 0

    @property
    def median_time(self) -> float:
        return statistics.median(self.times_ms) if self.times_ms else 0

    @property
    def std_dev(self) -> float:
        return statistics.stdev(self.times_ms) if len(self.times_ms) > 1 else 0

    # --- Extended statistics ---

    @property
    def coefficient_of_variation(self) -> float:
        """CV = std_dev / mean. Lower is more stable."""
        if self.avg_time == 0:
            return 0
        return self.std_dev / self.avg_time

    @property
    def percentile_5(self) -> float:
        return self._percentile(5)

    @property
    def percentile_25(self) -> float:
        return self._percentile(25)

    @property
    def percentile_75(self) -> float:
        return self._percentile(75)

    @property
    def percentile_95(self) -> float:
        return self._percentile(95)

    @property
    def percentile_99(self) -> float:
        return self._percentile(99)

    @property
    def iqr(self) -> float:
        """Interquartile range (P75 - P25)."""
        return self.percentile_75 - self.percentile_25

    @property
    def confidence_interval_95(self) -> tuple:
        """95% confidence interval for the mean (t-distribution)."""
        n = len(self.times_ms)
        if n < 2:
            return (self.avg_time, self.avg_time)
        se = self.std_dev / math.sqrt(n)
        # t-value for 95% CI approximation (good enough for n >= 10)
        t_val = _t_value_95(n - 1)
        margin = t_val * se
        return (self.avg_time - margin, self.avg_time + margin)

    @property
    def outlier_count(self) -> int:
        """Number of outliers detected using IQR method."""
        return len(self._detect_outliers())

    @property
    def times_without_outliers(self) -> List[float]:
        """Times with outliers removed."""
        outlier_indices = set(self._detect_outliers())
        return [t for i, t in enumerate(self.times_ms) if i not in outlier_indices]

    @property
    def avg_time_trimmed(self) -> float:
        """Mean excluding outliers."""
        trimmed = self.times_without_outliers
        return statistics.mean(trimmed) if trimmed else self.avg_time

    @property
    def success_rate(self) -> float:
        total = len(self.times_ms) + len(self.errors)
        if total == 0:
            return 0
        return (len(self.times_ms) / total) * 100

    @property
    def avg_row_count(self) -> float:
        return statistics.mean(self.row_counts) if self.row_counts else 0

    @property
    def consistent_row_count(self) -> bool:
        """True if all iterations returned the same row count."""
        if not self.row_counts:
            return True
        return len(set(self.row_counts)) == 1

    # --- Helpers ---

    def _percentile(self, p: int) -> float:
        if not self.times_ms:
            return 0
        sorted_times = sorted(self.times_ms)
        n = len(sorted_times)
        k = (p / 100) * (n - 1)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_times[int(k)]
        return sorted_times[f] * (c - k) + sorted_times[c] * (k - f)

    def _detect_outliers(self) -> List[int]:
        """Detect outliers using IQR method (1.5 * IQR)."""
        if len(self.times_ms) < 4:
            return []
        q1 = self._percentile(25)
        q3 = self._percentile(75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return [i for i, t in enumerate(self.times_ms) if t < lower or t > upper]

    def to_dict(self) -> Dict[str, Any]:
        ci_low, ci_high = self.confidence_interval_95
        return {
            'query_name': self.query_name,
            'query_description': self.query_description,
            'database': self.database,
            'category': self.category,
            'iterations': self.iterations,
            'warmup_iterations': self.warmup_iterations,
            # Core stats
            'min_time_ms': round(self.min_time, 3),
            'max_time_ms': round(self.max_time, 3),
            'avg_time_ms': round(self.avg_time, 3),
            'median_time_ms': round(self.median_time, 3),
            'std_dev_ms': round(self.std_dev, 3),
            # Extended stats
            'cv': round(self.coefficient_of_variation, 4),
            'p5_ms': round(self.percentile_5, 3),
            'p25_ms': round(self.percentile_25, 3),
            'p75_ms': round(self.percentile_75, 3),
            'p95_ms': round(self.percentile_95, 3),
            'p99_ms': round(self.percentile_99, 3),
            'iqr_ms': round(self.iqr, 3),
            'ci_95_lower_ms': round(ci_low, 3),
            'ci_95_upper_ms': round(ci_high, 3),
            'outlier_count': self.outlier_count,
            'avg_time_trimmed_ms': round(self.avg_time_trimmed, 3),
            # Result info
            'success_rate': round(self.success_rate, 1),
            'avg_row_count': round(self.avg_row_count, 1),
            'consistent_row_count': self.consistent_row_count,
            'error_count': len(self.errors)
        }


# =========================================================================
# Environment metadata
# =========================================================================
def collect_environment_metadata() -> Dict[str, Any]:
    """Collect system and runtime environment information."""
    return {
        'timestamp': datetime.now().isoformat(),
        'system': {
            'platform': platform.platform(),
            'processor': platform.processor(),
            'architecture': platform.machine(),
            'python_version': sys.version,
        },
        'benchmark_config': {
            'timer': 'time.perf_counter',
            'timer_resolution_ns': _get_timer_resolution(),
        }
    }


def _get_timer_resolution() -> float:
    """Estimate perf_counter resolution in nanoseconds."""
    try:
        return time.get_clock_info('perf_counter').resolution * 1e9
    except Exception:
        return -1


def _t_value_95(df: int) -> float:
    """Approximate t-value for 95% CI. Exact for common df, approximated otherwise."""
    # Pre-computed critical values for common degrees of freedom
    table = {
        1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
        6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        15: 2.131, 20: 2.086, 25: 2.060, 30: 2.042, 40: 2.021,
        50: 2.009, 60: 2.000, 80: 1.990, 100: 1.984, 200: 1.972,
    }
    if df in table:
        return table[df]
    # Interpolate or use closest
    if df > 200:
        return 1.960  # z-value for large samples
    keys = sorted(table.keys())
    for i in range(len(keys) - 1):
        if keys[i] < df < keys[i + 1]:
            # Linear interpolation
            frac = (df - keys[i]) / (keys[i + 1] - keys[i])
            return table[keys[i]] + frac * (table[keys[i + 1]] - table[keys[i]])
    return 1.960


# =========================================================================
# Base benchmark class
# =========================================================================
class BaseBenchmark(ABC):
    """Base class for database benchmarks."""

    DEFAULT_WARMUP_ITERATIONS = 3

    def __init__(self, database_name: str):
        self.database_name = database_name
        self.results: List[BenchmarkResult] = []

    @abstractmethod
    def connect(self) -> bool:
        """Connect to the database."""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the database."""
        pass

    @abstractmethod
    def warmup(self):
        """Warm up the database connection."""
        pass

    @abstractmethod
    def get_database_info(self) -> Dict[str, Any]:
        """Return database version and connection metadata."""
        pass

    def time_query(self, query_func: Callable, *args, **kwargs) -> QueryResult:
        """
        Time a single query execution.

        Args:
            query_func: Function to execute
            *args, **kwargs: Arguments to pass to the function

        Returns:
            QueryResult with timing and row count
        """
        start_time = time.perf_counter()
        try:
            result = query_func(*args, **kwargs)
            end_time = time.perf_counter()

            # Determine row count from result
            if isinstance(result, list):
                row_count = len(result)
            elif isinstance(result, dict):
                row_count = 1
            elif isinstance(result, int):
                row_count = result
            elif result is None:
                row_count = 0
            else:
                row_count = 1

            return QueryResult(
                query_name=query_func.__name__,
                execution_time_ms=(end_time - start_time) * 1000,
                row_count=row_count,
                success=True
            )
        except Exception as e:
            end_time = time.perf_counter()
            return QueryResult(
                query_name=query_func.__name__,
                execution_time_ms=(end_time - start_time) * 1000,
                row_count=0,
                success=False,
                error_message=str(e)
            )

    def run_benchmark(
        self,
        query_name: str,
        query_description: str,
        query_func: Callable,
        iterations: int = 10,
        *args,
        category: str = QueryCategory.POINT_LOOKUP,
        warmup_iterations: int = None,
        **kwargs
    ) -> BenchmarkResult:
        """
        Run a benchmark for a specific query.

        Args:
            query_name: Name of the query
            query_description: Description of what the query does
            query_func: Function to benchmark
            iterations: Number of measured iterations
            category: Query category for grouping
            warmup_iterations: Per-query warmup runs (discarded)
            *args, **kwargs: Arguments to pass to the query function

        Returns:
            BenchmarkResult with aggregated metrics
        """
        if warmup_iterations is None:
            warmup_iterations = self.DEFAULT_WARMUP_ITERATIONS

        result = BenchmarkResult(
            query_name=query_name,
            query_description=query_description,
            database=self.database_name,
            category=category,
            iterations=iterations,
            warmup_iterations=warmup_iterations
        )

        logger.info(f"Running benchmark: {query_name} "
                     f"({warmup_iterations} warmup + {iterations} measured)")

        # Warmup iterations (discarded)
        for _ in range(warmup_iterations):
            self.time_query(query_func, *args, **kwargs)

        # Measured iterations
        for i in range(iterations):
            query_result = self.time_query(query_func, *args, **kwargs)

            if query_result.success:
                result.times_ms.append(query_result.execution_time_ms)
                result.row_counts.append(query_result.row_count)
            else:
                result.errors.append(query_result.error_message)

        # Log summary
        if result.times_ms:
            ci_low, ci_high = result.confidence_interval_95
            logger.info(
                f"  {query_name}: "
                f"median={result.median_time:.2f}ms, "
                f"avg={result.avg_time:.2f}ms "
                f"[CI: {ci_low:.2f}-{ci_high:.2f}], "
                f"rows={result.avg_row_count:.0f}, "
                f"outliers={result.outlier_count}"
            )
        else:
            logger.warning(f"  {query_name}: ALL ITERATIONS FAILED")

        self.results.append(result)
        return result

    def get_all_results(self) -> List[Dict[str, Any]]:
        """Get all benchmark results as dictionaries."""
        return [r.to_dict() for r in self.results]

    def clear_results(self):
        """Clear all stored results."""
        self.results = []
