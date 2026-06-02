"""
Severity Classifier for Drug Interactions.

Classifies drug interactions into severity levels based on
the effect and recommendation text in Spanish.
"""
import re
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Drug interaction severity levels."""
    CONTRAINDICATED = "contraindicated"  # Must not be combined
    SEVERE = "severe"                     # Serious risk, avoid if possible
    MODERATE = "moderate"                 # Use with caution, monitor
    MILD = "mild"                         # Minor interaction, be aware
    UNKNOWN = "unknown"                   # Cannot determine


@dataclass
class SeverityResult:
    """Result of severity classification."""
    severity: Severity
    confidence: float
    matched_patterns: list
    reasoning: str


class SeverityClassifier:
    """
    Classifies drug interaction severity based on Spanish clinical text.

    Uses pattern matching with weighted rules to determine severity
    from effect and recommendation descriptions.
    """

    def __init__(self):
        """Initialize the severity classifier with Spanish patterns."""
        self._init_patterns()

    def _init_patterns(self):
        """Initialize classification patterns for Spanish text."""

        # Contraindicated patterns (highest severity)
        self.contraindicated_patterns = [
            (r'\bcontraindicad[ao]s?\b', 1.0),
            (r'\basociación\s+contraindicada\b', 1.0),
            (r'\bcombinación\s+contraindicada\b', 1.0),
            (r'\bno\s+debe\s+administrarse\b', 0.9),
            (r'\bno\s+deben\s+administrarse\s+conjuntamente\b', 1.0),
            (r'\bevitar\s+asociación\b', 0.9),
            (r'\bevitar\s+la\s+combinación\b', 0.9),
            (r'\bprohibid[ao]\b', 1.0),
            (r'\babsolutamente\s+contraindicad[ao]\b', 1.0),
        ]

        # Severe patterns
        self.severe_patterns = [
            (r'\briesgo\s+(?:de\s+)?muerte\b', 1.0),
            (r'\bmortal(?:es)?\b', 1.0),
            (r'\bletal(?:es)?\b', 1.0),
            (r'\bpotencialmente\s+(?:mortal|fatal)\b', 1.0),
            (r'\bparo\s+card[ií]aco\b', 0.95),
            (r'\barritmias?\s+(?:ventriculares?|graves?|severas?)\b', 0.9),
            (r'\btorsade\s+de\s+pointes\b', 0.95),
            (r'\bfibrilación\s+ventricular\b', 0.95),
            (r'\bhemorragia\s+(?:grave|severa|masiva|fatal)\b', 0.9),
            (r'\bshock\b', 0.85),
            (r'\binsuficiencia\s+(?:renal|hepática|respiratoria)\s+aguda\b', 0.85),
            (r'\bsíndrome\s+serotoninérgico\b', 0.85),
            (r'\bsíndrome\s+neuroléptico\s+maligno\b', 0.9),
            (r'\brabdomiólisis\b', 0.85),
            (r'\bagranulocitosis\b', 0.85),
            (r'\baplasia\s+medular\b', 0.9),
            (r'\bconvulsion(?:es)?\s+graves?\b', 0.85),
            (r'\bcoma\b', 0.85),
            (r'\briesgo\s+vital\b', 0.95),
            (r'\bamenaza\s+(?:para\s+)?la\s+vida\b', 0.95),
        ]

        # Moderate patterns
        self.moderate_patterns = [
            # "Asociación desaconsejada" is the most common CIMA phrase for a
            # moderate interaction (one level below "contraindicada").
            (r'\bdesaconsejad[ao]s?\b', 0.7),
            (r'\basociación\s+desaconsejada\b', 0.75),
            (r'\bprecaución\b', 0.7),
            (r'\bmonitorizar\b', 0.75),
            (r'\bvigilar\b', 0.7),
            (r'\bcontrolar\b', 0.65),
            (r'\bajustar\s+(?:la\s+)?dosis\b', 0.75),
            (r'\breducir\s+(?:la\s+)?dosis\b', 0.75),
            (r'\baumentar?\s+(?:el\s+)?riesgo\b', 0.7),
            (r'\bdisminuci[oó]n\s+del?\s+efecto\b', 0.65),
            (r'\breducci[oó]n\s+del?\s+efecto\b', 0.65),
            (r'\baumento\s+del?\s+efecto\b', 0.65),
            (r'\bpotenciación\b', 0.65),
            (r'\btoxicidad\b', 0.75),
            (r'\bhipotensión\b', 0.7),
            (r'\bhipertensión\b', 0.7),
            (r'\bhipoglucemia\b', 0.7),
            (r'\bhiperpotasemia\b', 0.75),
            (r'\bhemorragia\b', 0.75),
            (r'\bsangrado\b', 0.7),
            (r'\búlcera\b', 0.65),
            (r'\bnefrotoxicidad\b', 0.75),
            (r'\bhepatotoxicidad\b', 0.75),
            (r'\bmiopatía\b', 0.7),
            (r'\bse\s+recomienda\s+(?:vigilar|monitorizar|controlar)\b', 0.75),
            (r'\bevaluar\s+(?:el\s+)?riesgo\b', 0.7),
        ]

        # Mild patterns
        self.mild_patterns = [
            (r'\bleve(?:s|mente)?\b', 0.7),
            (r'\bmenor(?:es)?\b', 0.6),
            (r'\bmínimo\b', 0.7),
            (r'\bpoco\s+probable\b', 0.65),
            (r'\bimprobable\b', 0.65),
            (r'\bteóric[ao]\b', 0.6),
            (r'\bpotencial(?:mente)?\s+menor\b', 0.65),
            (r'\bno\s+(?:es\s+)?clínicamente\s+significativ[ao]\b', 0.75),
            (r'\bsin\s+relevancia\s+clínica\b', 0.75),
            (r'\bmolestias\s+(?:leves|menores)\b', 0.7),
            (r'\bpuede\s+no\s+ser\s+necesario\b', 0.6),
        ]

        # Compile all patterns
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self.compiled_patterns = {
            Severity.CONTRAINDICATED: [
                (re.compile(p, re.IGNORECASE), w)
                for p, w in self.contraindicated_patterns
            ],
            Severity.SEVERE: [
                (re.compile(p, re.IGNORECASE), w)
                for p, w in self.severe_patterns
            ],
            Severity.MODERATE: [
                (re.compile(p, re.IGNORECASE), w)
                for p, w in self.moderate_patterns
            ],
            Severity.MILD: [
                (re.compile(p, re.IGNORECASE), w)
                for p, w in self.mild_patterns
            ],
        }

    def classify(self, effect: str, recommendation: str = "") -> SeverityResult:
        """
        Classify the severity of a drug interaction.

        Args:
            effect: The effect description (Spanish text)
            recommendation: The recommendation text (Spanish text)

        Returns:
            SeverityResult with severity level and confidence
        """
        text = f"{effect} {recommendation}".strip()

        if not text:
            return SeverityResult(
                severity=Severity.UNKNOWN,
                confidence=0.0,
                matched_patterns=[],
                reasoning="No text provided for analysis"
            )

        # Score each severity level
        scores: Dict[Severity, Tuple[float, list]] = {}

        for severity, patterns in self.compiled_patterns.items():
            matches = []
            total_weight = 0.0

            for pattern, weight in patterns:
                found = pattern.findall(text)
                if found:
                    matches.extend(found)
                    total_weight += weight * len(found)

            if matches:
                scores[severity] = (total_weight, matches)

        # Determine severity based on hierarchy and scores
        if not scores:
            return SeverityResult(
                severity=Severity.UNKNOWN,
                confidence=0.3,
                matched_patterns=[],
                reasoning="No severity patterns matched"
            )

        # Priority order: contraindicated > severe > moderate > mild
        priority_order = [
            Severity.CONTRAINDICATED,
            Severity.SEVERE,
            Severity.MODERATE,
            Severity.MILD
        ]

        for severity in priority_order:
            if severity in scores:
                score, matches = scores[severity]

                # Calculate confidence based on score and pattern count
                base_confidence = min(0.95, 0.5 + (score * 0.1))

                # Boost confidence if multiple patterns match
                if len(matches) > 1:
                    base_confidence = min(0.98, base_confidence + 0.1)

                # Check for conflicting higher severity
                higher_severities = priority_order[:priority_order.index(severity)]
                has_higher = any(s in scores for s in higher_severities)

                if has_higher:
                    # Return the higher severity instead
                    for higher in higher_severities:
                        if higher in scores:
                            h_score, h_matches = scores[higher]
                            return SeverityResult(
                                severity=higher,
                                confidence=min(0.95, 0.5 + (h_score * 0.1)),
                                matched_patterns=h_matches,
                                reasoning=f"Matched {len(h_matches)} {higher.value} pattern(s)"
                            )

                return SeverityResult(
                    severity=severity,
                    confidence=base_confidence,
                    matched_patterns=matches,
                    reasoning=f"Matched {len(matches)} {severity.value} pattern(s)"
                )

        return SeverityResult(
            severity=Severity.UNKNOWN,
            confidence=0.3,
            matched_patterns=[],
            reasoning="Could not determine severity"
        )

    def classify_batch(self, interactions: list) -> list:
        """
        Classify multiple interactions.

        Args:
            interactions: List of dicts with 'effect' and 'recommendation' keys

        Returns:
            List of SeverityResult objects
        """
        results = []
        for interaction in interactions:
            effect = interaction.get('effect', interaction.get('efecto', ''))
            recommendation = interaction.get('recommendation', interaction.get('recomendacion', ''))
            results.append(self.classify(effect, recommendation))
        return results
