#!/usr/bin/env python3
"""
Compare NLP Approaches: Regex vs spaCy/NLTK.

This script compares the results of both NLP approaches on sample interactions
to help evaluate which approach works better for the specific use case.
"""

import os
import sys
import argparse
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.nlp import NLPPipeline  # Regex-based
from src.nlp_spacy import NLPPipelineSpacy  # spaCy-based
from src.utils.logger import setup_logging as setup_logger


# Sample interactions for testing (Spanish pharmaceutical text)
SAMPLE_INTERACTIONS = [
    {
        'id': 1,
        'efecto': 'Aumento del riesgo de arritmias ventriculares graves, incluyendo torsade de pointes.',
        'recomendacion': 'Asociación contraindicada. Se recomienda suspender uno de los principios activos.',
    },
    {
        'id': 2,
        'efecto': 'Aumento del riesgo de hemorragia digestiva.',
        'recomendacion': 'Precaución. Monitorizar signos de sangrado gastrointestinal.',
    },
    {
        'id': 3,
        'efecto': 'Disminución del efecto anticoagulante por inducción del metabolismo hepático mediado por CYP3A4.',
        'recomendacion': 'Ajustar dosis de anticoagulante. Monitorizar INR.',
    },
    {
        'id': 4,
        'efecto': 'Potenciación del efecto sedante sobre el SNC.',
        'recomendacion': 'Vigilar somnolencia excesiva. Evitar conducir.',
    },
    {
        'id': 5,
        'efecto': 'Riesgo de hiperpotasemia severa.',
        'recomendacion': 'Controlar niveles de potasio sérico. Evitar combinación en insuficiencia renal.',
    },
    {
        'id': 6,
        'efecto': 'Aumento de la nefrotoxicidad.',
        'recomendacion': 'Monitorizar función renal. Considerar alternativas.',
    },
    {
        'id': 7,
        'efecto': 'Síndrome serotoninérgico potencialmente mortal.',
        'recomendacion': 'Asociación contraindicada. No administrar conjuntamente.',
    },
    {
        'id': 8,
        'efecto': 'Posible prolongación del intervalo QT.',
        'recomendacion': 'Precaución en pacientes con factores de riesgo cardiovascular.',
    },
    {
        'id': 9,
        'efecto': 'Aumento leve de los niveles plasmáticos del fármaco.',
        'recomendacion': 'Generalmente no clínicamente significativo. Considerar monitorización.',
    },
    {
        'id': 10,
        'efecto': 'Inhibición del metabolismo por CYP2D6 con aumento de toxicidad.',
        'recomendacion': 'Reducir dosis. Vigilar efectos adversos.',
    },
]


def compare_single(regex_pipeline, spacy_pipeline, interaction: dict, logger) -> dict:
    """Compare both approaches on a single interaction."""
    effect = interaction['efecto']
    recommendation = interaction['recomendacion']

    # Process with regex approach
    regex_result = regex_pipeline.analyze(effect, recommendation)

    # Process with spaCy approach
    spacy_result = spacy_pipeline.analyze(effect, recommendation)

    return {
        'id': interaction['id'],
        'effect': effect[:60] + '...' if len(effect) > 60 else effect,
        'regex': {
            'severity': regex_result.severity,
            'severity_confidence': regex_result.severity_confidence,
            'type': regex_result.interaction_type,
            'mechanism': regex_result.mechanism_category,
            'overall_confidence': regex_result.overall_confidence,
        },
        'spacy': {
            'severity': spacy_result.severity,
            'severity_confidence': spacy_result.severity_confidence,
            'type': spacy_result.interaction_type,
            'mechanism': spacy_result.mechanism_category,
            'overall_confidence': spacy_result.overall_confidence,
            'enzymes': spacy_result.enzymes,
        },
        'match': {
            'severity': regex_result.severity == spacy_result.severity,
            'type': regex_result.interaction_type == spacy_result.interaction_type,
            'mechanism': regex_result.mechanism_category == spacy_result.mechanism_category,
        }
    }


def print_comparison(comparison: dict, logger):
    """Print formatted comparison."""
    logger.info(f"\n[{comparison['id']}] {comparison['effect']}")
    logger.info("-" * 70)

    # Severity comparison
    regex_sev = comparison['regex']['severity']
    spacy_sev = comparison['spacy']['severity']
    match_icon = "✓" if comparison['match']['severity'] else "✗"

    logger.info(f"  SEVERITY:   Regex: {regex_sev:<15} | spaCy: {spacy_sev:<15} [{match_icon}]")
    logger.info(f"              Conf:  {comparison['regex']['severity_confidence']:.2f}             "
               f"| Conf:  {comparison['spacy']['severity_confidence']:.2f}")

    # Type comparison
    regex_type = comparison['regex']['type']
    spacy_type = comparison['spacy']['type']
    match_icon = "✓" if comparison['match']['type'] else "✗"

    logger.info(f"  TYPE:       Regex: {regex_type:<15} | spaCy: {spacy_type:<15} [{match_icon}]")

    # Mechanism comparison
    regex_mech = comparison['regex']['mechanism']
    spacy_mech = comparison['spacy']['mechanism']
    match_icon = "✓" if comparison['match']['mechanism'] else "✗"

    logger.info(f"  MECHANISM:  Regex: {regex_mech:<15} | spaCy: {spacy_mech:<15} [{match_icon}]")

    # Additional spaCy info
    if comparison['spacy'].get('enzymes'):
        logger.info(f"  ENZYMES (spaCy only): {', '.join(comparison['spacy']['enzymes'])}")


def main():
    """Main comparison function."""
    parser = argparse.ArgumentParser(description='Compare NLP Approaches')
    parser.add_argument('--spacy-model', default='es_core_news_md',
                       choices=['es_core_news_sm', 'es_core_news_md', 'es_core_news_lg'],
                       help='spaCy model to use')
    parser.add_argument('--log-level', default='INFO')

    args = parser.parse_args()

    # Setup logging
    logger = setup_logger(args.log_level)

    logger.info("=" * 70)
    logger.info("NLP APPROACH COMPARISON: REGEX vs SPACY/NLTK")
    logger.info("=" * 70)

    # Initialize pipelines
    logger.info("\nInitializing pipelines...")
    logger.info("Loading Regex pipeline...")
    regex_pipeline = NLPPipeline()

    logger.info(f"Loading spaCy pipeline (model: {args.spacy_model})...")
    spacy_pipeline = NLPPipelineSpacy(args.spacy_model)

    # Compare on sample interactions
    logger.info("\n" + "=" * 70)
    logger.info("DETAILED COMPARISON")
    logger.info("=" * 70)

    all_comparisons = []
    for interaction in SAMPLE_INTERACTIONS:
        comparison = compare_single(regex_pipeline, spacy_pipeline, interaction, logger)
        all_comparisons.append(comparison)
        print_comparison(comparison, logger)

    # Summary statistics
    severity_matches = sum(1 for c in all_comparisons if c['match']['severity'])
    type_matches = sum(1 for c in all_comparisons if c['match']['type'])
    mechanism_matches = sum(1 for c in all_comparisons if c['match']['mechanism'])
    total = len(all_comparisons)

    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total samples: {total}")
    logger.info(f"Severity agreement: {severity_matches}/{total} ({severity_matches/total*100:.0f}%)")
    logger.info(f"Type agreement: {type_matches}/{total} ({type_matches/total*100:.0f}%)")
    logger.info(f"Mechanism agreement: {mechanism_matches}/{total} ({mechanism_matches/total*100:.0f}%)")

    # Average confidence comparison
    regex_conf = sum(c['regex']['overall_confidence'] for c in all_comparisons) / total
    spacy_conf = sum(c['spacy']['overall_confidence'] for c in all_comparisons) / total

    logger.info(f"\nAverage confidence:")
    logger.info(f"  Regex: {regex_conf:.2f}")
    logger.info(f"  spaCy: {spacy_conf:.2f}")

    logger.info("\n" + "=" * 70)
    logger.info("KEY DIFFERENCES")
    logger.info("=" * 70)
    logger.info("""
REGEX APPROACH:
  + Fast, no model loading required
  + Explicit patterns, easy to debug
  + Works offline without dependencies
  - Misses word variations not in patterns
  - No understanding of sentence structure

SPACY/NLTK APPROACH:
  + Handles word variations via lemmatization
  + Can detect negation and modifiers
  + Extracts entities (enzymes, transporters)
  + Uses linguistic features (POS, dependencies)
  - Requires model download (~40-150MB)
  - Slower initialization
  - More complex to debug
""")

    logger.info("=" * 70)


if __name__ == '__main__':
    main()
