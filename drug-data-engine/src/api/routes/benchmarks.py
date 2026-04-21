"""Database Performance / Benchmark endpoints."""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from src.api.schemas.responses import (
    BenchmarkSummary, BenchmarkQuery, CategoryBreakdown
)

router = APIRouter()


@router.get("", response_model=BenchmarkSummary)
async def get_benchmark_results():
    """Get the latest benchmark comparison results."""
    results_dir = Path(__file__).parent.parent.parent.parent / 'results'

    # Find the latest JSON results file
    json_files = sorted(results_dir.glob('benchmark_results_*.json'), reverse=True)
    if not json_files:
        raise HTTPException(
            status_code=404,
            detail="No benchmark results found. Run run_benchmarks.py first."
        )

    with open(json_files[0]) as f:
        data = json.load(f)

    comparison = data.get('comparison', [])
    metadata = data.get('metadata', {})

    queries = []
    mongodb_wins = 0
    neo4j_wins = 0
    comparable_count = 0
    mongodb_times = []
    neo4j_times = []
    row_count_mismatches = 0

    # Category tracking
    cat_stats = {}

    for item in comparison:
        mongo_ms = round(item['mongodb_median_ms'], 2) if item.get('mongodb_median_ms') else None
        neo4j_ms = round(item['neo4j_median_ms'], 2) if item.get('neo4j_median_ms') else None
        winner = item.get('winner', '')
        speedup_val = item.get('speedup_factor')
        speedup = f"{speedup_val:.2f}x" if speedup_val else None
        category = item.get('category', '')

        is_comparable = mongo_ms is not None and neo4j_ms is not None

        if is_comparable:
            comparable_count += 1
            if 'MongoDB' in winner:
                mongodb_wins += 1
            elif 'Neo4J' in winner or 'Neo4j' in winner:
                neo4j_wins += 1

            # Category breakdown
            if category not in cat_stats:
                cat_stats[category] = {'m': 0, 'n': 0, 'c': 0}
            if 'MongoDB' in winner:
                cat_stats[category]['m'] += 1
            elif 'Neo4J' in winner or 'Neo4j' in winner:
                cat_stats[category]['n'] += 1
            else:
                cat_stats[category]['c'] += 1

        if mongo_ms is not None:
            mongodb_times.append(mongo_ms)
        if neo4j_ms is not None:
            neo4j_times.append(neo4j_ms)

        if item.get('row_count_match') is False:
            row_count_mismatches += 1

        queries.append(BenchmarkQuery(
            query=item.get('query_name', ''),
            description=item.get('description', ''),
            category=category,
            mongodb_ms=mongo_ms,
            neo4j_ms=neo4j_ms,
            mongodb_p95_ms=round(item['mongodb_p95_ms'], 2) if item.get('mongodb_p95_ms') else None,
            neo4j_p95_ms=round(item['neo4j_p95_ms'], 2) if item.get('neo4j_p95_ms') else None,
            winner=winner,
            speedup=speedup,
            row_count_match=item.get('row_count_match'),
        ))

    mongodb_avg = round(sum(mongodb_times) / len(mongodb_times), 2) if mongodb_times else 0
    neo4j_avg = round(sum(neo4j_times) / len(neo4j_times), 2) if neo4j_times else 0

    # Determine overall winner with 10% threshold
    if mongodb_avg > 0 and neo4j_avg > 0:
        ratio = mongodb_avg / neo4j_avg
        speedup_factor = round(ratio, 2)
        if ratio > 1.10:
            overall_winner = 'Neo4j'
        elif ratio < 0.90:
            overall_winner = 'MongoDB'
        else:
            overall_winner = 'Comparable'
    else:
        overall_winner = 'N/A'
        speedup_factor = 0

    graph_exclusive = sum(1 for q in queries if q.winner == 'Neo4J only')

    category_breakdown = [
        CategoryBreakdown(
            category=cat,
            mongodb_wins=stats['m'],
            neo4j_wins=stats['n'],
            comparable=stats['c']
        )
        for cat, stats in sorted(cat_stats.items())
    ]

    return BenchmarkSummary(
        queries=queries,
        mongodb_wins=mongodb_wins,
        neo4j_wins=neo4j_wins,
        comparable_count=comparable_count,
        mongodb_avg_ms=mongodb_avg,
        neo4j_avg_ms=neo4j_avg,
        overall_winner=overall_winner,
        speedup_factor=speedup_factor,
        graph_exclusive_queries=graph_exclusive,
        category_breakdown=category_breakdown,
        iterations=metadata.get('iterations_per_query'),
        row_count_mismatches=row_count_mismatches,
    )


@router.get("/graph-stats")
async def get_graph_stats():
    """Get Neo4j graph statistics (node/relationship counts)."""
    from src.api.main import get_neo4j
    neo4j = get_neo4j()
    if not neo4j:
        raise HTTPException(status_code=503, detail="Neo4j is not connected")
    return neo4j.get_graph_stats()
