"""
Interaction Type Classifier for Drug Interactions.

Classifies drug interactions by their clinical effect type
based on Spanish pharmaceutical text.
"""
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class InteractionType(Enum):
    """Types of drug interaction effects."""
    CARDIAC = "cardiac"                    # Heart rhythm, QT, arrhythmias
    HEMORRHAGIC = "hemorrhagic"            # Bleeding risk
    CNS = "cns"                            # Central nervous system effects
    METABOLIC = "metabolic"                # Electrolytes, glucose, etc.
    RENAL = "renal"                        # Kidney function
    HEPATIC = "hepatic"                    # Liver function
    RESPIRATORY = "respiratory"            # Breathing effects
    GASTROINTESTINAL = "gastrointestinal"  # GI tract effects
    MUSCULAR = "muscular"                  # Muscle effects
    HEMATOLOGIC = "hematologic"            # Blood cell effects
    EFFICACY_REDUCTION = "efficacy_reduction"  # Reduced drug effect
    EFFICACY_INCREASE = "efficacy_increase"    # Enhanced drug effect
    TOXICITY = "toxicity"                  # General toxicity increase
    OTHER = "other"                        # Unclassified


@dataclass
class InteractionTypeResult:
    """Result of interaction type classification."""
    primary_type: InteractionType
    secondary_types: List[InteractionType]
    confidence: float
    matched_patterns: Dict[str, list]
    effect_category: str


class InteractionTypeClassifier:
    """
    Classifies drug interactions by clinical effect type.

    Analyzes Spanish pharmaceutical text to determine the
    primary clinical system or effect affected.
    """

    def __init__(self):
        """Initialize the interaction type classifier."""
        self._init_patterns()

    def _init_patterns(self):
        """Initialize classification patterns for each interaction type."""

        self.type_patterns = {
            InteractionType.CARDIAC: [
                r'\barritmias?\b',
                r'\btaquicardia\b',
                r'\bbradicardia\b',
                r'\bfibrilaci[oó]n\b',
                r'\bQT\b',
                r'\btorsade\b',
                r'\bcard[ií]ac[ao]s?\b',
                r'\bcoraz[oó]n\b',
                r'\binfarto\b',
                r'\bisquemia\s+card[ií]aca\b',
                r'\binsuficiencia\s+card[ií]aca\b',
                r'\bparo\s+card[ií]aco\b',
                r'\bbloqueo\s+(?:AV|auriculoventricular)\b',
                r'\bextras[ií]stoles?\b',
                r'\bvasoconstricción\s+coronaria\b',
            ],

            InteractionType.HEMORRHAGIC: [
                r'\bhemorragia\b',
                r'\bsangrado\b',
                r'\bhemorr[aá]gic[ao]\b',
                r'\banticoagula\w+\b',
                r'\bINR\b',
                r'\btiempo\s+de\s+protrombina\b',
                r'\bplaquetas?\b',
                r'\btrombocitopenia\b',
                r'\bequimosis\b',
                r'\bhematoma\b',
                r'\bepistaxis\b',
                r'\bmelena\b',
                r'\bhematemesis\b',
                r'\bpetequias\b',
            ],

            InteractionType.CNS: [
                r'\bsedaci[oó]n\b',
                r'\bsomnolencia\b',
                r'\bdepresi[oó]n\s+(?:del\s+)?SNC\b',
                r'\bconvulsi[oó]n(?:es)?\b',
                r'\bepilepsia\b',
                r'\bumbral\s+convulsivo\b',
                r'\bneurol[oó]gic[ao]\b',
                r'\bextrapiramidal(?:es)?\b',
                r'\bdiscinesia\b',
                r'\bdiston[ií]a\b',
                r'\bacatisia\b',
                r'\bparkinson\w*\b',
                r'\btemblor\b',
                r'\bataxia\b',
                r'\bconfusi[oó]n\b',
                r'\bdeliri[ou]m?\b',
                r'\balucina\w+\b',
                r'\bserotoninérgico\b',
                r'\bserotonina\b',
                r'\banticolin[eé]rgic[ao]\b',
                r'\bcoma\b',
                r'\bencefalopatía\b',
            ],

            InteractionType.METABOLIC: [
                r'\bhipopotasemia\b',
                r'\bhiperpotasemia\b',
                r'\bhiponatremia\b',
                r'\bhipernatremia\b',
                r'\bhipocalcemia\b',
                r'\bhipercalcemia\b',
                r'\bhipoglucemia\b',
                r'\bhiperglucemia\b',
                r'\belectrolit[ao]s?\b',
                r'\bacidosis\b',
                r'\balcalosis\b',
                r'\bhiperuricemia\b',
                r'\bgota\b',
                r'\bdeshidrataci[oó]n\b',
            ],

            InteractionType.RENAL: [
                r'\bnefrotoxic\w+\b',
                r'\binsuficiencia\s+renal\b',
                r'\bfunci[oó]n\s+renal\b',
                r'\baclaramiento\b',
                r'\bcreatinina\b',
                r'\bdiuresis\b',
                r'\boliguria\b',
                r'\banuria\b',
                r'\bnecrosis\s+tubular\b',
                r'\bnefritis\b',
                r'\bglomerul\w+\b',
            ],

            InteractionType.HEPATIC: [
                r'\bhepatotoxic\w+\b',
                r'\binsuficiencia\s+hep[aá]tica\b',
                r'\bfunci[oó]n\s+hep[aá]tica\b',
                r'\btransaminasas\b',
                r'\bALT\b',
                r'\bAST\b',
                r'\bbilirrubina\b',
                r'\bictericia\b',
                r'\bcolestasis\b',
                r'\bhepatitis\b',
                r'\bh[ií]gado\b',
            ],

            InteractionType.RESPIRATORY: [
                r'\bdepresi[oó]n\s+respiratoria\b',
                r'\bbroncoespasmo\b',
                r'\basma\b',
                r'\bdisnea\b',
                r'\bapnea\b',
                r'\bhipoxia\b',
                r'\binsuficiencia\s+respiratoria\b',
                r'\bneumon[ií]a\b',
                r'\bfibrosis\s+pulmonar\b',
            ],

            InteractionType.GASTROINTESTINAL: [
                r'\b[uú]lcera\s+(?:p[eé]ptica|g[aá]strica|duodenal)\b',
                r'\bgastritis\b',
                r'\bhemorragia\s+(?:digestiva|gastrointestinal)\b',
                r'\bn[aá]useas?\b',
                r'\bv[oó]mitos?\b',
                r'\bdiarrea\b',
                r'\bestre[nñ]imiento\b',
                r'\bpancreatitis\b',
                r'\bdispepsia\b',
                r'\bperforaci[oó]n\s+(?:g[aá]strica|intestinal)\b',
            ],

            InteractionType.MUSCULAR: [
                r'\bmiopat[ií]a\b',
                r'\brabdomi[oó]lisis\b',
                r'\bdebilidad\s+muscular\b',
                r'\bmialgia\b',
                r'\bcalambres?\b',
                r'\bCPK\b',
                r'\bcreatinfosfoquinasa\b',
                r'\bm[uú]sculo\b',
            ],

            InteractionType.HEMATOLOGIC: [
                r'\bagranulocitosis\b',
                r'\bneutropenia\b',
                r'\bleucop[eé]nia\b',
                r'\bpancitopenia\b',
                r'\baplasia\b',
                r'\banemia\b',
                r'\bm[eé]dula\s+[oó]sea\b',
                r'\bhematopoy[eé]tic[ao]\b',
            ],

            InteractionType.EFFICACY_REDUCTION: [
                r'\bdisminuci[oó]n\s+del?\s+efecto\b',
                r'\breducci[oó]n\s+del?\s+efecto\b',
                r'\bmenor\s+eficacia\b',
                r'\bp[eé]rdida\s+de\s+eficacia\b',
                r'\bantagonismo\b',
                r'\binhibici[oó]n\s+del?\s+efecto\b',
                r'\bfallo\s+terap[eé]utico\b',
                r'\bineficacia\b',
                r'\bdisminuye?\s+(?:la\s+)?absorci[oó]n\b',
                r'\bacelera?\s+(?:el\s+)?metabolismo\b',
            ],

            InteractionType.EFFICACY_INCREASE: [
                r'\baumento\s+del?\s+efecto\b',
                r'\bpotenciaci[oó]n\b',
                r'\bsinergismo\b',
                r'\bsinergia\b',
                r'\befecto\s+aditivo\b',
                r'\bmayor\s+efecto\b',
                r'\bincremento\s+del?\s+efecto\b',
                r'\benlentece?\s+(?:el\s+)?metabolismo\b',
                r'\binhibe?\s+(?:el\s+)?metabolismo\b',
            ],

            InteractionType.TOXICITY: [
                r'\btoxicidad\b',
                r'\bt[oó]xic[ao]\b',
                r'\bintoxicaci[oó]n\b',
                r'\bsobredosis\b',
                r'\bacumulaci[oó]n\b',
                r'\bniveles\s+(?:plasm[aá]ticos\s+)?elevados\b',
                r'\bconcentraciones?\s+elevad[ao]s?\b',
            ],
        }

        # Compile patterns
        self.compiled_patterns = {
            itype: [re.compile(p, re.IGNORECASE) for p in patterns]
            for itype, patterns in self.type_patterns.items()
        }

        # Effect category mapping
        self.effect_categories = {
            InteractionType.CARDIAC: "Cardiovascular",
            InteractionType.HEMORRHAGIC: "Hematological",
            InteractionType.CNS: "Neurological",
            InteractionType.METABOLIC: "Metabolic",
            InteractionType.RENAL: "Renal",
            InteractionType.HEPATIC: "Hepatic",
            InteractionType.RESPIRATORY: "Respiratory",
            InteractionType.GASTROINTESTINAL: "Gastrointestinal",
            InteractionType.MUSCULAR: "Musculoskeletal",
            InteractionType.HEMATOLOGIC: "Hematological",
            InteractionType.EFFICACY_REDUCTION: "Pharmacological",
            InteractionType.EFFICACY_INCREASE: "Pharmacological",
            InteractionType.TOXICITY: "Toxicological",
            InteractionType.OTHER: "Unclassified",
        }

    def classify(self, effect: str, recommendation: str = "") -> InteractionTypeResult:
        """
        Classify the type of drug interaction.

        Args:
            effect: The effect description (Spanish text)
            recommendation: The recommendation text (Spanish text)

        Returns:
            InteractionTypeResult with type classification
        """
        text = f"{effect} {recommendation}".strip()

        if not text:
            return InteractionTypeResult(
                primary_type=InteractionType.OTHER,
                secondary_types=[],
                confidence=0.0,
                matched_patterns={},
                effect_category="Unclassified"
            )

        # Score each type
        type_scores: Dict[InteractionType, tuple] = {}

        for itype, patterns in self.compiled_patterns.items():
            matches = []
            for pattern in patterns:
                found = pattern.findall(text)
                matches.extend(found)

            if matches:
                # Score based on number of matches
                score = len(matches)
                type_scores[itype] = (score, matches)

        if not type_scores:
            return InteractionTypeResult(
                primary_type=InteractionType.OTHER,
                secondary_types=[],
                confidence=0.3,
                matched_patterns={},
                effect_category="Unclassified"
            )

        # Sort by score
        sorted_types = sorted(
            type_scores.items(),
            key=lambda x: x[1][0],
            reverse=True
        )

        primary = sorted_types[0][0]
        primary_score, primary_matches = sorted_types[0][1]

        # Get secondary types (those with at least 1 match)
        secondary = [t for t, (s, m) in sorted_types[1:] if s >= 1]

        # Calculate confidence
        total_matches = sum(s for s, m in type_scores.values())
        confidence = min(0.95, 0.4 + (primary_score / max(total_matches, 1)) * 0.5)

        # Build matched patterns dict
        matched_patterns = {
            t.value: m for t, (s, m) in type_scores.items()
        }

        return InteractionTypeResult(
            primary_type=primary,
            secondary_types=secondary[:3],  # Limit to top 3 secondary
            confidence=confidence,
            matched_patterns=matched_patterns,
            effect_category=self.effect_categories[primary]
        )

    def classify_batch(self, interactions: list) -> list:
        """
        Classify multiple interactions.

        Args:
            interactions: List of dicts with 'effect' and 'recommendation' keys

        Returns:
            List of InteractionTypeResult objects
        """
        results = []
        for interaction in interactions:
            effect = interaction.get('effect', interaction.get('efecto', ''))
            recommendation = interaction.get('recommendation', interaction.get('recomendacion', ''))
            results.append(self.classify(effect, recommendation))
        return results
