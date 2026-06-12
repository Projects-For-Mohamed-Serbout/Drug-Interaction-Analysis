"""
NLP Evaluation Script — Precision, Recall, F1 per class.

Evaluates both NLP approaches (regex and spaCy) against a manually
annotated ground truth dataset of real drug interactions from CIMA.

This addresses Research Question 1 of the TFM:
  "Which NLP techniques are most effective for extracting and categorizing
   types of pharmacological interactions from textual data?"

Usage:
    python -m scripts.evaluate_nlp
    python -m scripts.evaluate_nlp --use-db            # sample from live DB
    python -m scripts.evaluate_nlp --output results/    # save report
"""
import argparse
import csv
import json
import logging
import hashlib
import random
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

from src.utils import setup_logging
from src.nlp import NLPPipeline
from src.nlp_spacy import NLPPipelineSpacy


# =========================================================================
# Ground Truth Dataset
#
# Each entry is a real interaction text from CIMA, annotated with the
# correct severity, type, and mechanism by domain analysis. The labels
# are determined by the clinical content of the Spanish text, following
# standard pharmacological classification criteria:
#
# SEVERITY:
#   contraindicated  — "Asociación contraindicada" or "no administrar"
#   severe           — "Asociación desaconsejada" with life-threatening effect
#   moderate         — "Asociación desaconsejada" / "precaución" / "monitorizar"
#   mild             — Minor interaction, generally not clinically significant
#   unknown          — Cannot be determined from the text
#
# TYPE: Classified by the primary organ system or pharmacological effect
# MECHANISM: pharmacokinetic / pharmacodynamic / unknown
# =========================================================================

GROUND_TRUTH = [
    # --- CONTRAINDICATED / CARDIAC ---
    {
        "efecto": "Aumento del riesgo de arritmias ventriculares.",
        "recomendacion": "Asociación contraindicada. Se recomienda suspender uno de los principios activos.",
        "true_severity": "contraindicated",
        "true_type": "cardiac",
        "true_mechanism": "pharmacodynamic",
    },
    {
        "efecto": "Riesgo de torsade de pointes.",
        "recomendacion": "Asociación contraindicada. Se recomienda suspender uno de los principios activos.",
        "true_severity": "contraindicated",
        "true_type": "cardiac",
        "true_mechanism": "pharmacodynamic",
    },
    {
        "efecto": "Posible prolongación del intervalo QT.",
        "recomendacion": "Precaución en pacientes con factores de riesgo cardiovascular.",
        "true_severity": "moderate",
        "true_type": "cardiac",
        "true_mechanism": "pharmacodynamic",
    },
    {
        "efecto": "Aumento del riesgo de arritmias ventriculares.",
        "recomendacion": "Asociación desaconsejada. Si es posible, suspender uno de los principios activos. Si no fuese posible, monitorizar el intervalo QT.",
        "true_severity": "moderate",
        "true_type": "cardiac",
        "true_mechanism": "pharmacodynamic",
    },
    # --- CONTRAINDICATED / CNS ---
    {
        "efecto": "Aumento del riesgo de síndrome serotoninérgico.",
        "recomendacion": "Asociación contraindicada. Se recomienda suspender uno de los principios activos.",
        "true_severity": "contraindicated",
        "true_type": "cns",
        "true_mechanism": "pharmacodynamic",
    },
    {
        "efecto": "Síndrome serotoninérgico potencialmente mortal.",
        "recomendacion": "Asociación contraindicada. No administrar conjuntamente.",
        "true_severity": "contraindicated",
        "true_type": "cns",
        "true_mechanism": "pharmacodynamic",
    },
    {
        "efecto": "Potenciación del efecto sedante sobre el SNC.",
        "recomendacion": "Vigilar somnolencia excesiva. Evitar conducir.",
        "true_severity": "moderate",
        "true_type": "cns",
        "true_mechanism": "pharmacodynamic",
    },
    {
        "efecto": "Aumento del riesgo de sedación.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento.",
        "true_severity": "moderate",
        "true_type": "cns",
        "true_mechanism": "unknown",
    },
    # --- CONTRAINDICATED / TOXICITY ---
    {
        "efecto": "Aumento del riesgo de toxicidad de colchicina.",
        "recomendacion": "Asociación contraindicada. Se recomienda suspender uno de los principios activos.",
        "true_severity": "contraindicated",
        "true_type": "toxicity",
        "true_mechanism": "unknown",
    },
    {
        "efecto": "Aumento del riesgo de toxicidad por metotrexato.",
        "recomendacion": "Asociación contraindicada. Se recomienda suspender uno de los principios activos.",
        "true_severity": "contraindicated",
        "true_type": "toxicity",
        "true_mechanism": "unknown",
    },
    # --- METABOLIC ---
    {
        "efecto": "Aumento del riesgo de hiperpotasemia.",
        "recomendacion": "Asociación contraindicada. Se recomienda suspender uno de los principios activos.",
        "true_severity": "contraindicated",
        "true_type": "metabolic",
        "true_mechanism": "unknown",
    },
    {
        "efecto": "Aumento del riesgo de hiperpotasemia.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento. En caso necesario, monitorizar los niveles de potasio.",
        "true_severity": "moderate",
        "true_type": "metabolic",
        "true_mechanism": "unknown",
    },
    {
        "efecto": "Riesgo de hiperpotasemia severa.",
        "recomendacion": "Controlar niveles de potasio sérico. Evitar combinación en insuficiencia renal.",
        "true_severity": "moderate",
        "true_type": "metabolic",
        "true_mechanism": "pharmacodynamic",
    },
    # --- HEMORRHAGIC ---
    {
        "efecto": "Aumento del riesgo de hemorragia digestiva.",
        "recomendacion": "Precaución. Monitorizar signos de sangrado gastrointestinal.",
        "true_severity": "moderate",
        "true_type": "hemorrhagic",
        "true_mechanism": "pharmacodynamic",
    },
    {
        "efecto": "Aumento del riesgo de úlcera péptica y hemorragia digestiva.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento.",
        "true_severity": "moderate",
        "true_type": "gastrointestinal",
        "true_mechanism": "pharmacodynamic",
    },
    # --- EFFICACY ---
    {
        "efecto": "Disminución del efecto anticoagulante por inducción del metabolismo hepático mediado por CYP3A4.",
        "recomendacion": "Ajustar dosis de anticoagulante. Monitorizar INR.",
        "true_severity": "moderate",
        "true_type": "efficacy_reduction",
        "true_mechanism": "pharmacokinetic",
    },
    {
        "efecto": "Disminución del efecto anticonceptivo.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento.",
        "true_severity": "moderate",
        "true_type": "efficacy_reduction",
        "true_mechanism": "unknown",
    },
    {
        "efecto": "Disminución del efecto uricosúrico.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento.",
        "true_severity": "moderate",
        "true_type": "efficacy_reduction",
        "true_mechanism": "unknown",
    },
    {
        "efecto": "Reducción del efecto de los dos antiinfecciosos.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento.",
        "true_severity": "moderate",
        "true_type": "efficacy_reduction",
        "true_mechanism": "unknown",
    },
    {
        "efecto": "Aumento del efecto anticoagulante y del riesgo hemorrágico.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento. Se recomienda monitorizar el INR.",
        "true_severity": "moderate",
        "true_type": "efficacy_increase",
        "true_mechanism": "unknown",
    },
    # --- RENAL ---
    {
        "efecto": "Aumento de la nefrotoxicidad.",
        "recomendacion": "Monitorizar función renal. Considerar alternativas.",
        "true_severity": "moderate",
        "true_type": "renal",
        "true_mechanism": "pharmacodynamic",
    },
    {
        "efecto": "Aumento del riesgo de nefrotoxicidad.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento. Se recomienda monitorizar la función renal.",
        "true_severity": "moderate",
        "true_type": "renal",
        "true_mechanism": "pharmacodynamic",
    },
    {
        "efecto": "Aumento de las concentraciones del inmunosupresor.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento. Se recomienda monitorizar la función renal y las concentraciones plasmáticas del inmunosupresor.",
        "true_severity": "moderate",
        "true_type": "toxicity",
        "true_mechanism": "pharmacokinetic",
    },
    # --- HEPATIC ---
    {
        "efecto": "Aumento del riesgo de hepatotoxicidad.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento. Monitorizar pruebas de función hepática.",
        "true_severity": "moderate",
        "true_type": "hepatic",
        "true_mechanism": "unknown",
    },
    # --- MUSCULAR ---
    {
        "efecto": "Aumento del riesgo de rabdomiólisis.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento.",
        "true_severity": "moderate",
        "true_type": "muscular",
        "true_mechanism": "unknown",
    },
    # --- PHARMACOKINETIC MECHANISMS ---
    {
        "efecto": "Inhibición del metabolismo por CYP2D6 con aumento de toxicidad.",
        "recomendacion": "Reducir dosis. Vigilar efectos adversos.",
        "true_severity": "moderate",
        "true_type": "toxicity",
        "true_mechanism": "pharmacokinetic",
    },
    {
        "efecto": "Aumento de las concentraciones plasmáticas de quetiapina.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento.",
        "true_severity": "moderate",
        "true_type": "toxicity",
        "true_mechanism": "pharmacokinetic",
    },
    {
        "efecto": "Aumento de las concentraciones del inmunosupresor.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento.",
        "true_severity": "moderate",
        "true_type": "toxicity",
        "true_mechanism": "pharmacokinetic",
    },
    # --- SEVERE (life-threatening effect but not explicitly "contraindicada") ---
    {
        "efecto": "Aumento del riesgo de muerte súbita cardíaca.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento.",
        "true_severity": "severe",
        "true_type": "cardiac",
        "true_mechanism": "pharmacodynamic",
    },
    {
        "efecto": "Riesgo de depresión respiratoria grave.",
        "recomendacion": "Asociación desaconsejada. Monitorizar estrechamente la función respiratoria.",
        "true_severity": "severe",
        "true_type": "cns",
        "true_mechanism": "pharmacodynamic",
    },
    {
        "efecto": "Aumento del riesgo de hemorragia cerebral.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento.",
        "true_severity": "severe",
        "true_type": "hemorrhagic",
        "true_mechanism": "pharmacodynamic",
    },
    {
        "efecto": "Riesgo de insuficiencia hepática aguda.",
        "recomendacion": "Asociación desaconsejada. Monitorizar función hepática estrechamente.",
        "true_severity": "severe",
        "true_type": "hepatic",
        "true_mechanism": "unknown",
    },
    # --- MILD ---
    {
        "efecto": "Aumento leve de los niveles plasmáticos del fármaco.",
        "recomendacion": "Generalmente no clínicamente significativo. Considerar monitorización.",
        "true_severity": "mild",
        "true_type": "toxicity",
        "true_mechanism": "pharmacokinetic",
    },
    {
        "efecto": "Posible disminución leve de la absorción.",
        "recomendacion": "Sin relevancia clínica. No requiere ajuste de dosis.",
        "true_severity": "mild",
        "true_type": "efficacy_reduction",
        "true_mechanism": "pharmacokinetic",
    },
    {
        "efecto": "Ligero aumento de los niveles séricos sin significación clínica.",
        "recomendacion": "No se requiere ajuste posológico.",
        "true_severity": "mild",
        "true_type": "other",
        "true_mechanism": "pharmacokinetic",
    },
    # --- UNKNOWN (ambiguous text, cannot determine severity) ---
    {
        "efecto": "Posible modificación de los efectos del fármaco.",
        "recomendacion": "Valorar ajuste según respuesta clínica.",
        "true_severity": "unknown",
        "true_type": "other",
        "true_mechanism": "unknown",
    },
    {
        "efecto": "Interacción de significación clínica desconocida.",
        "recomendacion": "Se desconoce la relevancia clínica.",
        "true_severity": "unknown",
        "true_type": "other",
        "true_mechanism": "unknown",
    },
    # --- OTHER / COMPLEX ---
    {
        "efecto": "Aumento del riesgo de hipertensión de rebote cuando se suspende la clonidina, empeorada por la presencia de un beta bloqueante.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento. Interrumpir el tratamiento con el beta bloqueante algunos días antes de iniciar la suspensión gradual de la clonidina.",
        "true_severity": "moderate",
        "true_type": "cardiac",
        "true_mechanism": "pharmacodynamic",
    },
    {
        "efecto": "Aumento del riesgo de toxicidad por fenitoína.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento. Se recomienda monitorizar niveles de fenitoína.",
        "true_severity": "moderate",
        "true_type": "toxicity",
        "true_mechanism": "pharmacokinetic",
    },
    # --- CONTRAINDICATED / OTHER ---
    {
        "efecto": "Riesgo de vasoconstricción coronaria.",
        "recomendacion": "Asociación contraindicada. Se recomienda suspender uno de los principios activos.",
        "true_severity": "contraindicated",
        "true_type": "cardiac",
        "true_mechanism": "pharmacodynamic",
    },
    {
        "efecto": "Aumento del riesgo de ergotismo.",
        "recomendacion": "Asociación contraindicada. Se recomienda suspender uno de los principios activos.",
        "true_severity": "contraindicated",
        "true_type": "toxicity",
        "true_mechanism": "unknown",
    },
    {
        "efecto": "Aumento del riesgo de miopatía y rabdomiólisis.",
        "recomendacion": "Asociación contraindicada. Se recomienda suspender uno de los principios activos.",
        "true_severity": "contraindicated",
        "true_type": "muscular",
        "true_mechanism": "unknown",
    },
    {
        "efecto": "Aumento del riesgo de nefrotoxicidad y ototoxicidad.",
        "recomendacion": "Asociación desaconsejada. Valorar el beneficio/riesgo del tratamiento. Se recomienda monitorizar la función renal y auditiva.",
        "true_severity": "moderate",
        "true_type": "renal",
        "true_mechanism": "pharmacodynamic",
    },
    {
        "efecto": "Aumento del riesgo de hipoglucemia.",
        "recomendacion": "Precaución. Monitorizar la glucemia.",
        "true_severity": "moderate",
        "true_type": "metabolic",
        "true_mechanism": "pharmacodynamic",
    },
]


# =========================================================================
# External gold set (annotated CSV from scripts.sample_gold_set)
# =========================================================================

def load_gold_csv(path: str, logger) -> List[Dict]:
    """
    Load an annotated gold set produced by scripts.sample_gold_set.

    Only rows with all three labels filled are kept. Returns the same shape as
    the built-in GROUND_TRUTH so the rest of the pipeline is unchanged.
    """
    rows: List[Dict] = []
    skipped = 0
    # utf-8-sig tolerates the BOM written for Excel compatibility
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            sev = (row.get("true_severity") or "").strip().lower()
            typ = (row.get("true_type") or "").strip().lower()
            mech = (row.get("true_mechanism") or "").strip().lower()
            if not (sev and typ and mech):
                skipped += 1
                continue
            rows.append({
                "efecto": (row.get("efecto") or "").strip(),
                "recomendacion": (row.get("recomendacion") or "").strip(),
                "true_severity": sev,
                "true_type": typ,
                "true_mechanism": mech,
            })
    logger.info("Loaded %d annotated rows from %s (skipped %d unlabelled).",
                len(rows), path, skipped)
    if not rows:
        raise ValueError(
            f"No fully-annotated rows in {path}. Fill true_severity / "
            f"true_type / true_mechanism before evaluating."
        )
    return rows


# =========================================================================
# Evaluation metrics
# =========================================================================

def compute_metrics(
    y_true: List[str], y_pred: List[str], label: str
) -> Dict[str, any]:
    """Compute precision, recall, F1 for each class and macro/weighted avg."""
    classes = sorted(set(y_true) | set(y_pred))
    per_class = {}

    for cls in classes:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p == cls)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != cls and p == cls)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p != cls)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        per_class[cls] = {
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'f1': round(f1, 3),
            'support': sum(1 for t in y_true if t == cls),
            'tp': tp, 'fp': fp, 'fn': fn,
        }

    # Macro average (only over classes with ground truth support)
    supported = {c: m for c, m in per_class.items() if m['support'] > 0}
    n_supported = len(supported) if supported else 1
    macro_p = sum(m['precision'] for m in supported.values()) / n_supported
    macro_r = sum(m['recall'] for m in supported.values()) / n_supported
    macro_f1 = sum(m['f1'] for m in supported.values()) / n_supported

    # Weighted average
    total = len(y_true)
    weighted_p = sum(m['precision'] * m['support'] for m in per_class.values()) / total
    weighted_r = sum(m['recall'] * m['support'] for m in per_class.values()) / total
    weighted_f1 = sum(m['f1'] * m['support'] for m in per_class.values()) / total

    accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / total

    return {
        'label': label,
        'per_class': per_class,
        'macro': {'precision': round(macro_p, 3), 'recall': round(macro_r, 3), 'f1': round(macro_f1, 3)},
        'weighted': {'precision': round(weighted_p, 3), 'recall': round(weighted_r, 3), 'f1': round(weighted_f1, 3)},
        'accuracy': round(accuracy, 3),
        'total_samples': total,
    }


def print_metrics(metrics: Dict, logger):
    """Print classification report."""
    logger.info(f"\n{'='*70}")
    logger.info(f"  {metrics['label']}")
    logger.info(f"{'='*70}")
    logger.info(f"  {'Class':<20} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
    logger.info(f"  {'-'*60}")

    for cls, m in sorted(metrics['per_class'].items()):
        if m['support'] == 0 and m['fp'] == 0:
            continue  # Skip classes with no ground truth and no predictions
        suffix = "  *" if m['support'] == 0 else ""
        logger.info(f"  {cls:<20} {m['precision']:>10.3f} {m['recall']:>10.3f} "
                     f"{m['f1']:>10.3f} {m['support']:>10}{suffix}")

    logger.info(f"  {'-'*60}")
    m = metrics['macro']
    logger.info(f"  {'macro avg':<20} {m['precision']:>10.3f} {m['recall']:>10.3f} {m['f1']:>10.3f}")
    w = metrics['weighted']
    logger.info(f"  {'weighted avg':<20} {w['precision']:>10.3f} {w['recall']:>10.3f} {w['f1']:>10.3f}")
    logger.info(f"  {'accuracy':<20} {'':>10} {'':>10} {metrics['accuracy']:>10.3f}")
    logger.info(f"  Total samples: {metrics['total_samples']}")

    # Flag phantom classes
    phantoms = [c for c, m in metrics['per_class'].items() if m['support'] == 0 and m['fp'] > 0]
    if phantoms:
        logger.info(f"  * No ground truth support (false positives only): {', '.join(phantoms)}")


def build_confusion_matrix(y_true: List[str], y_pred: List[str]) -> Tuple[List[str], List[List[int]]]:
    """Build a confusion matrix."""
    classes = sorted(set(y_true) | set(y_pred))
    matrix = [[0] * len(classes) for _ in classes]
    cls_idx = {c: i for i, c in enumerate(classes)}
    for t, p in zip(y_true, y_pred):
        matrix[cls_idx[t]][cls_idx[p]] += 1
    return classes, matrix


def print_confusion_matrix(classes: List[str], matrix: List[List[int]], title: str, logger):
    """Print confusion matrix."""
    logger.info(f"\n  Confusion Matrix — {title}")
    # Header
    header = "  " + f"{'True \\ Pred':<18}" + "".join(f"{c[:10]:>12}" for c in classes)
    logger.info(header)
    logger.info("  " + "-" * (18 + 12 * len(classes)))
    for i, cls in enumerate(classes):
        row = "  " + f"{cls:<18}" + "".join(f"{matrix[i][j]:>12}" for j in range(len(classes)))
        logger.info(row)


# =========================================================================
# Main
# =========================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='Evaluate NLP approaches')
    parser.add_argument('--output', type=str, default=None,
                        help='Directory to save results (JSON)')
    parser.add_argument('--gold-csv', type=str, default=None,
                        help='Annotated gold-set CSV (from scripts.sample_gold_set). '
                             'If omitted, uses the built-in 44-sample set.')
    parser.add_argument('--spacy-model', default='es_core_news_md')
    parser.add_argument('--log-level', default='INFO')
    return parser.parse_args()


def main():
    args = parse_args()
    logger = setup_logging(args.log_level)

    # --- Select gold set: external annotated CSV or the built-in sample ---
    if args.gold_csv:
        gold = load_gold_csv(args.gold_csv, logger)
        gold_source = args.gold_csv
    else:
        gold = GROUND_TRUTH
        gold_source = "built-in (44 curated samples)"

    logger.info("=" * 70)
    logger.info("NLP EVALUATION: Regex vs spaCy against Ground Truth")
    logger.info(f"Gold set: {gold_source}")
    logger.info(f"Ground truth samples: {len(gold)}")
    logger.info("=" * 70)

    # --- Distribution of ground truth ---
    sev_dist = Counter(s['true_severity'] for s in gold)
    type_dist = Counter(s['true_type'] for s in gold)
    mech_dist = Counter(s['true_mechanism'] for s in gold)

    logger.info("\nGround truth distribution:")
    logger.info(f"  Severity: {dict(sev_dist)}")
    logger.info(f"  Type:     {dict(type_dist)}")
    logger.info(f"  Mechanism: {dict(mech_dist)}")

    # --- Initialize pipelines ---
    logger.info("\nInitializing NLP pipelines...")
    regex_pipeline = NLPPipeline()
    spacy_pipeline = NLPPipelineSpacy(args.spacy_model)
    logger.info("Pipelines ready.")

    # --- Run both approaches ---
    regex_severities, regex_types, regex_mechanisms = [], [], []
    spacy_severities, spacy_types, spacy_mechanisms = [], [], []
    true_severities, true_types, true_mechanisms = [], [], []

    details = []

    for sample in gold:
        effect = sample['efecto']
        recom = sample['recomendacion']

        regex_result = regex_pipeline.analyze(effect, recom)
        spacy_result = spacy_pipeline.analyze(effect, recom)

        true_severities.append(sample['true_severity'])
        true_types.append(sample['true_type'])
        true_mechanisms.append(sample['true_mechanism'])

        regex_severities.append(regex_result.severity)
        regex_types.append(regex_result.interaction_type)
        regex_mechanisms.append(regex_result.mechanism_category)

        spacy_severities.append(spacy_result.severity)
        spacy_types.append(spacy_result.interaction_type)
        spacy_mechanisms.append(spacy_result.mechanism_category)

        details.append({
            'effect': effect[:80],
            'true': {
                'severity': sample['true_severity'],
                'type': sample['true_type'],
                'mechanism': sample['true_mechanism'],
            },
            'regex': {
                'severity': regex_result.severity,
                'type': regex_result.interaction_type,
                'mechanism': regex_result.mechanism_category,
                'confidence': round(regex_result.overall_confidence, 3),
            },
            'spacy': {
                'severity': spacy_result.severity,
                'type': spacy_result.interaction_type,
                'mechanism': spacy_result.mechanism_category,
                'confidence': round(spacy_result.overall_confidence, 3),
            },
        })

    # --- Compute metrics ---
    regex_sev_metrics = compute_metrics(true_severities, regex_severities, "SEVERITY — Regex")
    spacy_sev_metrics = compute_metrics(true_severities, spacy_severities, "SEVERITY — spaCy")

    regex_type_metrics = compute_metrics(true_types, regex_types, "TYPE — Regex")
    spacy_type_metrics = compute_metrics(true_types, spacy_types, "TYPE — spaCy")

    regex_mech_metrics = compute_metrics(true_mechanisms, regex_mechanisms, "MECHANISM — Regex")
    spacy_mech_metrics = compute_metrics(true_mechanisms, spacy_mechanisms, "MECHANISM — spaCy")

    # --- Print results ---
    logger.info("\n" + "#" * 70)
    logger.info("#  CLASSIFICATION REPORTS")
    logger.info("#" * 70)

    for m in [regex_sev_metrics, spacy_sev_metrics,
              regex_type_metrics, spacy_type_metrics,
              regex_mech_metrics, spacy_mech_metrics]:
        print_metrics(m, logger)

    # --- Confusion matrices ---
    logger.info("\n" + "#" * 70)
    logger.info("#  CONFUSION MATRICES")
    logger.info("#" * 70)

    for y_true, y_pred, title in [
        (true_severities, regex_severities, "Severity — Regex"),
        (true_severities, spacy_severities, "Severity — spaCy"),
        (true_types, regex_types, "Type — Regex"),
        (true_types, spacy_types, "Type — spaCy"),
    ]:
        classes, matrix = build_confusion_matrix(y_true, y_pred)
        print_confusion_matrix(classes, matrix, title, logger)

    # --- Head-to-head summary ---
    logger.info("\n" + "#" * 70)
    logger.info("#  HEAD-TO-HEAD COMPARISON")
    logger.info("#" * 70)

    logger.info(f"\n  {'Metric':<25} {'Regex':>12} {'spaCy':>12} {'Winner':>12}")
    logger.info(f"  {'-'*61}")

    comparisons = [
        ("Severity Accuracy", regex_sev_metrics['accuracy'], spacy_sev_metrics['accuracy']),
        ("Severity Macro-F1", regex_sev_metrics['macro']['f1'], spacy_sev_metrics['macro']['f1']),
        ("Type Accuracy", regex_type_metrics['accuracy'], spacy_type_metrics['accuracy']),
        ("Type Macro-F1", regex_type_metrics['macro']['f1'], spacy_type_metrics['macro']['f1']),
        ("Mechanism Accuracy", regex_mech_metrics['accuracy'], spacy_mech_metrics['accuracy']),
        ("Mechanism Macro-F1", regex_mech_metrics['macro']['f1'], spacy_mech_metrics['macro']['f1']),
    ]

    regex_wins = 0
    spacy_wins = 0
    for name, regex_val, spacy_val in comparisons:
        if regex_val > spacy_val:
            winner = "Regex"
            regex_wins += 1
        elif spacy_val > regex_val:
            winner = "spaCy"
            spacy_wins += 1
        else:
            winner = "Tie"
        logger.info(f"  {name:<25} {regex_val:>12.3f} {spacy_val:>12.3f} {winner:>12}")

    logger.info(f"\n  Overall: Regex wins {regex_wins}, spaCy wins {spacy_wins}")

    # --- Misclassification analysis ---
    logger.info("\n" + "#" * 70)
    logger.info("#  MISCLASSIFICATION DETAILS (severity)")
    logger.info("#" * 70)

    for d in details:
        regex_wrong = d['true']['severity'] != d['regex']['severity']
        spacy_wrong = d['true']['severity'] != d['spacy']['severity']
        if regex_wrong or spacy_wrong:
            logger.info(f"\n  Effect: {d['effect']}...")
            logger.info(f"  True: {d['true']['severity']}")
            if regex_wrong:
                logger.info(f"  Regex predicted: {d['regex']['severity']} (WRONG)")
            if spacy_wrong:
                logger.info(f"  spaCy predicted: {d['spacy']['severity']} (WRONG)")

    # --- Save results ---
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"nlp_evaluation_{timestamp}.json"

        # Attach confusion matrices (classes + matrix) to each metrics block
        for metrics, yt, yp in [
            (regex_sev_metrics, true_severities, regex_severities),
            (spacy_sev_metrics, true_severities, spacy_severities),
            (regex_type_metrics, true_types, regex_types),
            (spacy_type_metrics, true_types, spacy_types),
            (regex_mech_metrics, true_mechanisms, regex_mechanisms),
            (spacy_mech_metrics, true_mechanisms, spacy_mechanisms),
        ]:
            classes, matrix = build_confusion_matrix(yt, yp)
            metrics['confusion'] = {'classes': classes, 'matrix': matrix}

        report = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'ground_truth_samples': len(gold),
                'gold_source': gold_source,
                'spacy_model': args.spacy_model,
            },
            'results': {
                'severity': {
                    'regex': regex_sev_metrics,
                    'spacy': spacy_sev_metrics,
                },
                'type': {
                    'regex': regex_type_metrics,
                    'spacy': spacy_type_metrics,
                },
                'mechanism': {
                    'regex': regex_mech_metrics,
                    'spacy': spacy_mech_metrics,
                },
            },
            'details': details,
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"\nResults saved to: {output_file}")

    logger.info("\n" + "=" * 70)
    logger.info("EVALUATION COMPLETE")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
