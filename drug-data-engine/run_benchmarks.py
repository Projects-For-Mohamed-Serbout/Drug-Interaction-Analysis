"""
Benchmark Runner for MongoDB vs Neo4J Performance Comparison.

Runs all benchmarks on both databases and generates comprehensive
comparison reports with statistical analysis.

Usage:
    python run_benchmarks.py                    # Run all (30 iterations)
    python run_benchmarks.py --iterations 50    # Run with 50 iterations
    python run_benchmarks.py --mongodb-only     # Run only MongoDB benchmarks
    python run_benchmarks.py --neo4j-only       # Run only Neo4J benchmarks
    python run_benchmarks.py --output report    # Custom output prefix
"""
import argparse
import json
import sys
import csv
from datetime import datetime
from pathlib import Path
import logging

from src.config import get_settings
from src.utils import setup_logging
from src.benchmarks import MongoDBBenchmark, Neo4JBenchmark
from src.benchmarks.base_benchmark import collect_environment_metadata


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Database Benchmark Runner — MongoDB vs Neo4J',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--iterations',
        type=int,
        default=30,
        help='Number of measured iterations per query (default: 30)'
    )
    parser.add_argument(
        '--mongodb-only',
        action='store_true',
        help='Run only MongoDB benchmarks'
    )
    parser.add_argument(
        '--neo4j-only',
        action='store_true',
        help='Run only Neo4J benchmarks'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='benchmark_results',
        help='Output filename prefix (default: benchmark_results)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )

    return parser.parse_args()


def run_mongodb_benchmarks(settings, iterations: int, logger) -> tuple:
    """Run MongoDB benchmarks. Returns (results_list, db_info_dict)."""
    logger.info("=" * 60)
    logger.info("MONGODB BENCHMARKS")
    logger.info("=" * 60)

    benchmark = MongoDBBenchmark(
        uri=settings.mongodb_uri,
        database=settings.mongodb_db
    )

    if not benchmark.connect():
        logger.error("Failed to connect to MongoDB")
        return [], {}

    try:
        db_info = benchmark.get_database_info()
        logger.info(f"MongoDB version: {db_info.get('version', 'unknown')}")
        benchmark.warmup()
        benchmark.run_all_benchmarks(iterations=iterations)
        return benchmark.get_all_results(), db_info
    finally:
        benchmark.disconnect()


def run_neo4j_benchmarks(settings, iterations: int, logger) -> tuple:
    """Run Neo4J benchmarks. Returns (results_list, db_info_dict)."""
    logger.info("=" * 60)
    logger.info("NEO4J BENCHMARKS")
    logger.info("=" * 60)

    benchmark = Neo4JBenchmark(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password
    )

    if not benchmark.connect():
        logger.error("Failed to connect to Neo4J")
        return [], {}

    try:
        db_info = benchmark.get_database_info()
        logger.info(f"Neo4J version: {db_info.get('version', 'unknown')}")
        benchmark.warmup()
        benchmark.run_all_benchmarks(iterations=iterations)
        return benchmark.get_all_results(), db_info
    finally:
        benchmark.disconnect()


def create_comparison_table(mongodb_results: list, neo4j_results: list) -> list:
    """Create a detailed comparison table between MongoDB and Neo4J results."""
    comparison = []
    neo4j_lookup = {r['query_name']: r for r in neo4j_results}

    for mongo_result in mongodb_results:
        query_name = mongo_result['query_name']
        neo4j_result = neo4j_lookup.get(query_name)

        row = {
            'query_name': query_name,
            'description': mongo_result['query_description'],
            'category': mongo_result['category'],
            # MongoDB metrics
            'mongodb_avg_ms': mongo_result['avg_time_ms'],
            'mongodb_median_ms': mongo_result['median_time_ms'],
            'mongodb_p95_ms': mongo_result['p95_ms'],
            'mongodb_min_ms': mongo_result['min_time_ms'],
            'mongodb_max_ms': mongo_result['max_time_ms'],
            'mongodb_std_dev_ms': mongo_result['std_dev_ms'],
            'mongodb_cv': mongo_result['cv'],
            'mongodb_rows': mongo_result['avg_row_count'],
        }

        if neo4j_result:
            row.update({
                'neo4j_avg_ms': neo4j_result['avg_time_ms'],
                'neo4j_median_ms': neo4j_result['median_time_ms'],
                'neo4j_p95_ms': neo4j_result['p95_ms'],
                'neo4j_min_ms': neo4j_result['min_time_ms'],
                'neo4j_max_ms': neo4j_result['max_time_ms'],
                'neo4j_std_dev_ms': neo4j_result['std_dev_ms'],
                'neo4j_cv': neo4j_result['cv'],
                'neo4j_rows': neo4j_result['avg_row_count'],
            })

            # Row count validation
            row['row_count_match'] = _row_counts_match(
                mongo_result['avg_row_count'],
                neo4j_result['avg_row_count']
            )

            # Winner determination using median (more robust than mean)
            mongo_median = mongo_result['median_time_ms']
            neo4j_median = neo4j_result['median_time_ms']

            if mongo_median > 0 and neo4j_median > 0:
                speedup = mongo_median / neo4j_median
                row['speedup_factor'] = round(speedup, 2)
                # Only declare winner if difference is statistically meaningful
                # Use > 10% threshold to avoid noise-driven conclusions
                if speedup > 1.10:
                    row['winner'] = 'Neo4J'
                elif speedup < 0.90:
                    row['winner'] = 'MongoDB'
                else:
                    row['winner'] = 'Comparable'
            else:
                row['speedup_factor'] = 0
                row['winner'] = 'N/A'
        else:
            row.update({
                'neo4j_avg_ms': None, 'neo4j_median_ms': None,
                'neo4j_p95_ms': None, 'neo4j_min_ms': None,
                'neo4j_max_ms': None, 'neo4j_std_dev_ms': None,
                'neo4j_cv': None, 'neo4j_rows': None,
                'speedup_factor': None, 'winner': 'MongoDB only',
                'row_count_match': None,
            })

        comparison.append(row)

    # Add Neo4J-only queries (graph-specific)
    for neo4j_result in neo4j_results:
        query_name = neo4j_result['query_name']
        if not any(r['query_name'] == query_name for r in comparison):
            comparison.append({
                'query_name': query_name,
                'description': neo4j_result['query_description'],
                'category': neo4j_result['category'],
                'mongodb_avg_ms': None, 'mongodb_median_ms': None,
                'mongodb_p95_ms': None, 'mongodb_min_ms': None,
                'mongodb_max_ms': None, 'mongodb_std_dev_ms': None,
                'mongodb_cv': None, 'mongodb_rows': None,
                'neo4j_avg_ms': neo4j_result['avg_time_ms'],
                'neo4j_median_ms': neo4j_result['median_time_ms'],
                'neo4j_p95_ms': neo4j_result['p95_ms'],
                'neo4j_min_ms': neo4j_result['min_time_ms'],
                'neo4j_max_ms': neo4j_result['max_time_ms'],
                'neo4j_std_dev_ms': neo4j_result['std_dev_ms'],
                'neo4j_cv': neo4j_result['cv'],
                'neo4j_rows': neo4j_result['avg_row_count'],
                'speedup_factor': None,
                'winner': 'Neo4J only',
                'row_count_match': None,
            })

    return comparison


def _row_counts_match(mongo_rows, neo4j_rows) -> bool:
    """Check if row counts are consistent (allows for minor floating-point diffs)."""
    if mongo_rows == 0 and neo4j_rows == 0:
        return True
    if mongo_rows == 0 or neo4j_rows == 0:
        return False
    ratio = min(mongo_rows, neo4j_rows) / max(mongo_rows, neo4j_rows)
    return ratio >= 0.90  # Allow 10% tolerance for limit-based queries


def print_comparison_table(comparison: list, logger):
    """Print formatted comparison table to console."""
    logger.info("")
    logger.info("=" * 120)
    logger.info("BENCHMARK COMPARISON: MongoDB vs Neo4J")
    logger.info("=" * 120)

    # Header
    header = (f"{'Query':<32} {'Category':<22} {'MongoDB':<12} {'Neo4J':<12} "
              f"{'Speedup':<10} {'Winner':<12} {'Rows OK'}")
    logger.info(header)
    logger.info("-" * 120)

    for row in comparison:
        mongo_time = f"{row['mongodb_median_ms']:.1f}" if row['mongodb_median_ms'] is not None else "---"
        neo4j_time = f"{row['neo4j_median_ms']:.1f}" if row['neo4j_median_ms'] is not None else "---"
        speedup = f"{row['speedup_factor']:.2f}x" if row['speedup_factor'] is not None else "---"
        winner = row['winner'] or "N/A"
        category = row.get('category', '')[:20]
        rows_ok = ""
        if row.get('row_count_match') is not None:
            rows_ok = "yes" if row['row_count_match'] else "MISMATCH"

        line = (f"{row['query_name']:<32} {category:<22} {mongo_time:<12} "
                f"{neo4j_time:<12} {speedup:<10} {winner:<12} {rows_ok}")
        logger.info(line)

    logger.info("-" * 120)
    logger.info("  Times shown are MEDIAN (ms). Speedup = MongoDB_median / Neo4J_median.")
    logger.info("  Winner requires >10% difference; otherwise 'Comparable'.")


def print_summary(comparison: list, logger):
    """Print summary statistics with category breakdown."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)

    # Count winners (only comparable queries)
    comparable = [r for r in comparison
                  if r['mongodb_median_ms'] is not None
                  and r['neo4j_median_ms'] is not None]

    mongodb_wins = sum(1 for r in comparable if r['winner'] == 'MongoDB')
    neo4j_wins = sum(1 for r in comparable if r['winner'] == 'Neo4J')
    ties = sum(1 for r in comparable if r['winner'] == 'Comparable')
    neo4j_exclusive = sum(1 for r in comparison if r['winner'] == 'Neo4J only')

    logger.info(f"Comparable queries: {len(comparable)}")
    logger.info(f"  MongoDB wins:   {mongodb_wins}")
    logger.info(f"  Neo4J wins:     {neo4j_wins}")
    logger.info(f"  Comparable:     {ties}")
    logger.info(f"Graph-exclusive queries (Neo4J only): {neo4j_exclusive}")

    # Average times for comparable queries
    if comparable:
        avg_mongodb = sum(r['mongodb_median_ms'] for r in comparable) / len(comparable)
        avg_neo4j = sum(r['neo4j_median_ms'] for r in comparable) / len(comparable)

        logger.info("")
        logger.info("Overall median times (comparable queries):")
        logger.info(f"  MongoDB: {avg_mongodb:.2f} ms")
        logger.info(f"  Neo4J:   {avg_neo4j:.2f} ms")

        overall_speedup = avg_mongodb / avg_neo4j if avg_neo4j > 0 else 0
        if overall_speedup > 1.10:
            logger.info(f"  Overall: Neo4J is {overall_speedup:.2f}x faster")
        elif overall_speedup < 0.90:
            logger.info(f"  Overall: MongoDB is {1/overall_speedup:.2f}x faster")
        else:
            logger.info(f"  Overall: Comparable performance")

    # Category breakdown
    logger.info("")
    logger.info("BY CATEGORY:")
    logger.info("-" * 60)
    categories = sorted(set(r.get('category', '') for r in comparable if r.get('category')))
    for cat in categories:
        cat_queries = [r for r in comparable if r.get('category') == cat]
        if not cat_queries:
            continue
        cat_mongo_wins = sum(1 for r in cat_queries if r['winner'] == 'MongoDB')
        cat_neo4j_wins = sum(1 for r in cat_queries if r['winner'] == 'Neo4J')
        cat_ties = sum(1 for r in cat_queries if r['winner'] == 'Comparable')
        logger.info(f"  {cat:<25} M:{cat_mongo_wins} N:{cat_neo4j_wins} ~:{cat_ties}")

    # Row count validation
    mismatches = [r for r in comparable if r.get('row_count_match') is False]
    if mismatches:
        logger.info("")
        logger.info("ROW COUNT MISMATCHES (investigate query equivalency):")
        for r in mismatches:
            logger.info(
                f"  {r['query_name']}: MongoDB={r['mongodb_rows']:.0f}, "
                f"Neo4J={r['neo4j_rows']:.0f}"
            )
    else:
        logger.info("")
        logger.info("Row count validation: ALL QUERIES MATCH")

    # Data quality warnings
    high_cv = [r for r in comparable
               if (r.get('mongodb_cv') or 0) > 0.5
               or (r.get('neo4j_cv') or 0) > 0.5]
    if high_cv:
        logger.info("")
        logger.info("HIGH VARIABILITY WARNINGS (CV > 0.5):")
        for r in high_cv:
            parts = []
            if (r.get('mongodb_cv') or 0) > 0.5:
                parts.append(f"MongoDB CV={r['mongodb_cv']:.2f}")
            if (r.get('neo4j_cv') or 0) > 0.5:
                parts.append(f"Neo4J CV={r['neo4j_cv']:.2f}")
            logger.info(f"  {r['query_name']}: {', '.join(parts)}")


def save_results(
    mongodb_results: list,
    neo4j_results: list,
    comparison: list,
    env_metadata: dict,
    mongodb_info: dict,
    neo4j_info: dict,
    iterations: int,
    output_prefix: str,
    logger
):
    """Save results to JSON and CSV files."""
    # Ensure results directory exists
    results_dir = Path(__file__).parent / 'results'
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # --- JSON: Full results with metadata ---
    json_file = results_dir / f"{output_prefix}_{timestamp}.json"
    full_results = {
        'metadata': {
            **env_metadata,
            'iterations_per_query': iterations,
            'warmup_iterations_per_query': 3,
            'comparable_queries': sum(
                1 for r in comparison
                if r.get('mongodb_median_ms') is not None
                and r.get('neo4j_median_ms') is not None
            ),
            'graph_exclusive_queries': sum(
                1 for r in comparison if r['winner'] == 'Neo4J only'
            ),
        },
        'database_info': {
            'mongodb': mongodb_info,
            'neo4j': neo4j_info,
        },
        'mongodb_results': mongodb_results,
        'neo4j_results': neo4j_results,
        'comparison': comparison,
    }

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(full_results, f, indent=2, ensure_ascii=False)
    logger.info(f"Full results saved to: {json_file}")

    # --- CSV: Comparison table ---
    csv_file = results_dir / f"{output_prefix}_{timestamp}.csv"
    if comparison:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=comparison[0].keys())
            writer.writeheader()
            writer.writerows(comparison)
        logger.info(f"Comparison CSV saved to: {csv_file}")


def main():
    """Main entry point."""
    args = parse_args()
    logger = setup_logging(args.log_level)

    logger.info("=" * 60)
    logger.info("DATABASE BENCHMARK: MongoDB vs Neo4J")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Iterations per query: {args.iterations}")
    logger.info(f"Warmup iterations per query: 3 (discarded)")
    logger.info("=" * 60)

    if args.iterations < 10:
        logger.warning(
            f"Low iteration count ({args.iterations}). "
            "Recommend >= 30 for statistically reliable results."
        )

    # Collect environment metadata
    env_metadata = collect_environment_metadata()

    # Load settings
    settings = get_settings()

    mongodb_results = []
    neo4j_results = []
    mongodb_info = {}
    neo4j_info = {}

    # Run benchmarks
    if not args.neo4j_only:
        mongodb_results, mongodb_info = run_mongodb_benchmarks(
            settings, args.iterations, logger
        )

    if not args.mongodb_only:
        neo4j_results, neo4j_info = run_neo4j_benchmarks(
            settings, args.iterations, logger
        )

    # Create comparison
    comparison = []
    if mongodb_results and neo4j_results:
        comparison = create_comparison_table(mongodb_results, neo4j_results)
        print_comparison_table(comparison, logger)
        print_summary(comparison, logger)
    elif mongodb_results:
        logger.info("Only MongoDB results available (no comparison)")
    elif neo4j_results:
        logger.info("Only Neo4J results available (no comparison)")
    else:
        logger.error("No benchmark results available")
        sys.exit(1)

    # Save results
    save_results(
        mongodb_results, neo4j_results, comparison,
        env_metadata, mongodb_info, neo4j_info,
        args.iterations, args.output, logger
    )

    logger.info("")
    logger.info("=" * 60)
    logger.info("BENCHMARK COMPLETE")
    logger.info(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
