"""
Severity Classifier using spaCy and NLTK - IMPROVED VERSION.

This implementation uses:
- spaCy for tokenization, lemmatization, POS tagging, and dependency parsing
- NLTK for additional text processing
- BOTH token matching AND lemma matching for comprehensive coverage
- Phrase pattern detection for clinical recommendations
- NEGATION DETECTION to handle phrases like "no se espera interacción"
"""

import spacy
import re
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import logging
import nltk
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Drug interaction severity levels."""
    CONTRAINDICATED = "contraindicated"
    SEVERE = "severe"
    MODERATE = "moderate"
    MILD = "mild"
    UNKNOWN = "unknown"


@dataclass
class SeverityResult:
    """Result of severity classification."""
    severity: Severity
    confidence: float
    matched_terms: List[str]
    linguistic_features: Dict
    reasoning: str


class SeverityClassifierSpacy:
    """
    Classifies drug interaction severity using spaCy and NLTK.

    IMPROVED VERSION - Key changes:
    1. Matches BOTH original tokens AND lemmas
    2. Uses regex patterns for key phrases (like "asociación contraindicada")
    3. Higher weights for explicit clinical recommendations
    4. Better handling of compound terms
    5. NEGATION DETECTION - detects "no", "sin", "ninguna" to reduce severity
    """

    def __init__(self, model_name: str = "es_core_news_md"):
        """Initialize the spaCy-based severity classifier."""
        self.model_name = model_name
        self._load_models()
        self._init_severity_lexicons()
        self._init_phrase_patterns()
        self._init_negation_patterns()

    def _load_models(self):
        """Load spaCy model and NLTK resources."""
        try:
            self.nlp = spacy.load(self.model_name)
            logger.info(f"Loaded spaCy model: {self.model_name}")
        except OSError:
            logger.warning(f"Model {self.model_name} not found, downloading...")
            spacy.cli.download(self.model_name)
            self.nlp = spacy.load(self.model_name)

        # Download NLTK resources
        for resource in ['punkt', 'stopwords']:
            try:
                nltk.data.find(f'tokenizers/{resource}' if resource == 'punkt' else f'corpora/{resource}')
            except LookupError:
                nltk.download(resource, quiet=True)

        try:
            self.spanish_stopwords = set(stopwords.words('spanish'))
        except:
            nltk.download('stopwords', quiet=True)
            self.spanish_stopwords = set(stopwords.words('spanish'))

    def _init_phrase_patterns(self):
        """
        Initialize regex patterns for detecting key clinical phrases.

        These patterns catch multi-word expressions that indicate severity.
        """
        # CONTRAINDICATED phrase patterns (highest priority)
        self.contraindicated_patterns = [
            # Direct contraindication statements
            (re.compile(r'\bcontraindicad[ao]s?\b', re.IGNORECASE), 2.0),
            (re.compile(r'\basociaci[oó]n\s+contraindicada\b', re.IGNORECASE), 2.5),
            (re.compile(r'\bcombinaci[oó]n\s+contraindicada\b', re.IGNORECASE), 2.5),
            (re.compile(r'\buso\s+contraindicado\b', re.IGNORECASE), 2.5),
            # Prohibition statements
            (re.compile(r'\bno\s+(?:se\s+)?debe[n]?\s+administrar(?:se)?\s+(?:conjuntamente|simult[aá]neamente)\b', re.IGNORECASE), 2.0),
            (re.compile(r'\bno\s+administrar\s+conjuntamente\b', re.IGNORECASE), 2.0),
            (re.compile(r'\bevitar\s+(?:la\s+)?(?:asociaci[oó]n|combinaci[oó]n|uso\s+conjunto)\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bprohibid[ao]\b', re.IGNORECASE), 2.0),
            (re.compile(r'\babsolutamente\s+contraindicad[ao]\b', re.IGNORECASE), 2.5),
            # Suspension recommendations
            (re.compile(r'\bsuspender\s+(?:uno\s+de\s+)?(?:los\s+)?(?:principios?\s+activos?|medicamentos?|f[aá]rmacos?)\b', re.IGNORECASE), 1.5),
        ]

        # SEVERE phrase patterns
        self.severe_patterns = [
            # Life-threatening conditions
            (re.compile(r'\briesgo\s+(?:de\s+)?muerte\b', re.IGNORECASE), 2.0),
            (re.compile(r'\bpotencialmente\s+(?:mortal|fatal|letal)\b', re.IGNORECASE), 2.0),
            (re.compile(r'\bamenaza\s+(?:para\s+)?la\s+vida\b', re.IGNORECASE), 2.0),
            (re.compile(r'\briesgo\s+vital\b', re.IGNORECASE), 2.0),
            # Specific severe conditions
            (re.compile(r'\btorsade[s]?\s+de\s+pointes\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bs[ií]ndrome\s+serotonin[eé]rgico\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bs[ií]ndrome\s+neurol[eé]ptico\s+maligno\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bparo\s+card[ií]aco\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bfibrilaci[oó]n\s+ventricular\b', re.IGNORECASE), 1.8),
            (re.compile(r'\barritmias?\s+(?:ventriculares?\s+)?(?:graves?|severas?|mortales?)\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bhemorragia\s+(?:grave|severa|masiva|fatal|cerebral)\b', re.IGNORECASE), 1.5),
            (re.compile(r'\binsuficiencia\s+(?:renal|hep[aá]tica|respiratoria|card[ií]aca)\s+aguda\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bshock\s+(?:anafil[aá]ctico|s[eé]ptico|cardiog[eé]nico)?\b', re.IGNORECASE), 1.5),
        ]

        # MODERATE phrase patterns
        self.moderate_patterns = [
            # "Asociación desaconsejada": most common CIMA moderate-severity phrase
            # (one level below "contraindicada").
            (re.compile(r'\bdesaconsejad[ao]s?\b', re.IGNORECASE), 1.0),
            (re.compile(r'\basociaci[oó]n\s+desaconsejada\b', re.IGNORECASE), 1.1),
            (re.compile(r'\breducci[oó]n\s+del?\s+efecto\b', re.IGNORECASE), 0.8),
            (re.compile(r'\bprecauci[oó]n\b', re.IGNORECASE), 1.0),
            (re.compile(r'\bmonitorizar\b', re.IGNORECASE), 1.0),
            (re.compile(r'\bvigilar\b', re.IGNORECASE), 0.9),
            (re.compile(r'\bse\s+recomienda\s+(?:vigilar|monitorizar|controlar)\b', re.IGNORECASE), 1.2),
            (re.compile(r'\bajustar\s+(?:la\s+)?dosis\b', re.IGNORECASE), 1.0),
            (re.compile(r'\breducir\s+(?:la\s+)?dosis\b', re.IGNORECASE), 1.0),
            (re.compile(r'\baumento\s+del?\s+riesgo\b', re.IGNORECASE), 0.9),
            (re.compile(r'\bdisminuci[oó]n\s+del?\s+efecto\b', re.IGNORECASE), 0.8),
            (re.compile(r'\baumento\s+del?\s+efecto\b', re.IGNORECASE), 0.8),
            (re.compile(r'\bevaluar\s+(?:el\s+)?riesgo\b', re.IGNORECASE), 0.9),
        ]

        # MILD phrase patterns
        self.mild_patterns = [
            (re.compile(r'\bleve(?:mente|s)?\b', re.IGNORECASE), 1.0),
            (re.compile(r'\bpoco\s+probable\b', re.IGNORECASE), 1.0),
            (re.compile(r'\bno\s+(?:es\s+)?cl[ií]nicamente\s+significativ[ao]\b', re.IGNORECASE), 1.2),
            (re.compile(r'\bsin\s+relevancia\s+cl[ií]nica\b', re.IGNORECASE), 1.2),
            (re.compile(r'\bm[ií]nim[ao]\b', re.IGNORECASE), 0.9),
            (re.compile(r'\bimprobable\b', re.IGNORECASE), 0.9),
            (re.compile(r'\bgeneralmente\s+no\s+(?:es\s+)?(?:necesario|significativo)\b', re.IGNORECASE), 1.0),
        ]

    def _init_negation_patterns(self):
        """
        Initialize negation detection patterns.

        Negation phrases indicate LOW severity (mild/none) when they negate
        severity-indicating words. For example:
        - "No se espera interacción" → mild
        - "Sin relevancia clínica" → mild
        - "No requiere ajuste" → mild
        """
        # Negation words (Spanish)
        self.negation_words = {
            'no', 'sin', 'ningún', 'ningun', 'ninguna', 'ninguno',
            'nunca', 'jamás', 'jamas', 'tampoco', 'ni',
        }

        # Negation phrase patterns that indicate LOW/MILD severity
        self.negation_mild_patterns = [
            # "No se espera interacción"
            (re.compile(r'\bno\s+se\s+(?:espera|prevé|preve|anticipa)\s+(?:ninguna?\s+)?interacci[oó]n\b', re.IGNORECASE), 2.5),
            # "No se han descrito interacciones"
            (re.compile(r'\bno\s+se\s+(?:han?\s+)?(?:descrito|observado|detectado|reportado)\s+interacci[oó]n(?:es)?\b', re.IGNORECASE), 2.5),
            # "Sin interacción clínicamente significativa"
            (re.compile(r'\bsin\s+interacci[oó]n(?:es)?\s+(?:cl[ií]nicamente\s+)?significativ[ao]s?\b', re.IGNORECASE), 2.5),
            # "No clínicamente significativo"
            (re.compile(r'\bno\s+(?:es\s+)?cl[ií]nicamente\s+significativ[ao]\b', re.IGNORECASE), 2.0),
            # "Sin relevancia clínica"
            (re.compile(r'\bsin\s+relevancia\s+cl[ií]nica\b', re.IGNORECASE), 2.0),
            # "No requiere ajuste de dosis"
            (re.compile(r'\bno\s+(?:se\s+)?requiere\s+(?:ajuste|modificaci[oó]n)\s+(?:de\s+)?(?:la\s+)?dosis\b', re.IGNORECASE), 1.8),
            # "No es necesario ajustar"
            (re.compile(r'\bno\s+(?:es\s+)?necesario\s+(?:ajustar|modificar|cambiar)\b', re.IGNORECASE), 1.8),
            # "Sin efectos adversos significativos"
            (re.compile(r'\bsin\s+efectos?\s+(?:adversos?\s+)?significativ[ao]s?\b', re.IGNORECASE), 1.8),
            # "No produce/causa interacción"
            (re.compile(r'\bno\s+(?:se\s+)?(?:produce|causa|genera|origina)\s+(?:ninguna?\s+)?interacci[oó]n\b', re.IGNORECASE), 2.0),
            # "Interacción poco probable"
            (re.compile(r'\binteracci[oó]n\s+(?:poco|muy\s+poco)\s+probable\b', re.IGNORECASE), 2.0),
            # "Riesgo bajo/mínimo"
            (re.compile(r'\briesgo\s+(?:bajo|m[ií]nimo|insignificante|despreciable)\b', re.IGNORECASE), 1.5),
            # "No hay evidencia de interacción"
            (re.compile(r'\bno\s+(?:hay|existe)\s+(?:evidencia|datos?)\s+(?:de\s+)?interacci[oó]n\b', re.IGNORECASE), 2.0),
        ]

        # Patterns where negation INCREASES severity (e.g., "no administrar" = contraindicated)
        self.negation_contraindicated_patterns = [
            # "No administrar conjuntamente" - this is CONTRAINDICATED, not mild
            (re.compile(r'\bno\s+(?:se\s+)?(?:debe[n]?\s+)?administrar(?:se)?\s+(?:conjuntamente|simult[aá]neamente|juntos?)\b', re.IGNORECASE), 2.5),
            # "No asociar" / "No combinar"
            (re.compile(r'\bno\s+(?:se\s+)?(?:debe[n]?\s+)?(?:asociar|combinar|mezclar)\b', re.IGNORECASE), 2.0),
            # "No usar conjuntamente"
            (re.compile(r'\bno\s+(?:se\s+)?(?:debe[n]?\s+)?usar(?:se)?\s+(?:conjuntamente|juntos?)\b', re.IGNORECASE), 2.0),
        ]

    def _detect_negation(self, doc, text: str) -> Dict:
        """
        Detect negation in text using spaCy dependency parsing and patterns.

        Returns:
            Dict with:
            - has_negation_mild: True if negation indicates mild severity
            - has_negation_contraindicated: True if negation indicates contraindicated
            - negation_score_mild: Score boost for mild severity
            - negation_score_contraindicated: Score boost for contraindicated
            - negated_terms: List of terms that are negated
        """
        result = {
            'has_negation_mild': False,
            'has_negation_contraindicated': False,
            'negation_score_mild': 0.0,
            'negation_score_contraindicated': 0.0,
            'negated_terms': [],
        }

        # 1. Check negation patterns that indicate MILD severity
        for pattern, weight in self.negation_mild_patterns:
            matches = pattern.findall(text)
            if matches:
                result['has_negation_mild'] = True
                result['negation_score_mild'] += weight * len(matches)
                result['negated_terms'].extend(matches)

        # 2. Check negation patterns that indicate CONTRAINDICATED
        for pattern, weight in self.negation_contraindicated_patterns:
            matches = pattern.findall(text)
            if matches:
                result['has_negation_contraindicated'] = True
                result['negation_score_contraindicated'] += weight * len(matches)
                result['negated_terms'].extend(matches)

        # 3. Use spaCy dependency parsing to detect negation relationships
        for token in doc:
            # Check if token is a negation word
            if token.text.lower() in self.negation_words or token.dep_ == 'neg':
                # Find what is being negated (the head of the negation)
                head = token.head

                # Check if the negated word is a severity indicator
                head_text = head.text.lower()
                head_lemma = head.lemma_.lower()

                # If negating severity words, this indicates mild
                severity_words = {'significativo', 'significativa', 'importante',
                                  'relevante', 'grave', 'severo', 'severa'}
                if head_text in severity_words or head_lemma in severity_words:
                    result['has_negation_mild'] = True
                    result['negation_score_mild'] += 1.5
                    result['negated_terms'].append(f"negated:{head_text}")

        return result

    def _init_severity_lexicons(self):
        """
        Initialize severity lexicons with BOTH tokens and lemmas.

        Key improvement: Include original word forms, not just lemmas.
        """
        # CONTRAINDICATED - tokens AND lemmas
        self.contraindicated_tokens = {
            # Original tokens (as they appear in text)
            'contraindicada', 'contraindicado', 'contraindicadas', 'contraindicados',
            'prohibido', 'prohibida', 'prohibidos', 'prohibidas',
        }
        self.contraindicated_lemmas = {
            'contraindicar', 'prohibir',
        }

        # SEVERE - tokens AND lemmas
        self.severe_tokens = {
            'muerte', 'mortal', 'mortales', 'letal', 'letales', 'fatal', 'fatales',
            'paro', 'shock', 'coma',
            'arritmia', 'arritmias', 'fibrilacion', 'fibrilación',
            'hemorragia', 'hemorragias',
            'convulsion', 'convulsión', 'convulsiones',
            'rabdomiolisis', 'rabdomiólisis',
            'agranulocitosis', 'aplasia',
        }
        self.severe_lemmas = {
            'morir', 'fallecer',
        }

        # MODERATE - tokens AND lemmas
        self.moderate_tokens = {
            'desaconsejada', 'desaconsejado', 'desaconsejadas', 'desaconsejados',
            'precaución', 'precaucion',
            'monitorizar', 'monitorización', 'monitorizacion',
            'vigilar', 'vigilancia',
            'controlar', 'control',
            'ajustar', 'ajuste',
            'reducir', 'reducción', 'reduccion',
            'toxicidad',
            'hipotensión', 'hipotension', 'hipertensión', 'hipertension',
            'hipoglucemia', 'hiperpotasemia', 'hipopotasemia',
            'sangrado', 'sangrados',
            'nefrotoxicidad', 'hepatotoxicidad',
            'miopatía', 'miopatia',
        }
        self.moderate_lemmas = {
            'monitorizar', 'vigilar', 'controlar', 'ajustar', 'reducir', 'desaconsejar',
        }

        # MILD - tokens AND lemmas
        self.mild_tokens = {
            'leve', 'leves', 'levemente',
            'menor', 'menores',
            'mínimo', 'minimo', 'mínima', 'minima',
            'improbable', 'improbables',
            'teórico', 'teorico', 'teórica', 'teorica',
            'insignificante', 'insignificantes',
        }
        self.mild_lemmas = {
            'leve', 'menor', 'mínimo',
        }

        # Intensifiers and diminishers
        self.intensifiers = {
            'muy', 'altamente', 'extremadamente', 'gravemente',
            'severamente', 'potencialmente', 'significativamente',
            'marcadamente', 'notablemente', 'considerablemente',
        }
        self.diminishers = {
            'poco', 'ligeramente', 'levemente', 'apenas',
            'raramente', 'escasamente', 'mínimamente',
        }

    def _score_patterns(self, text: str, patterns: List[Tuple]) -> Tuple[float, List[str]]:
        """Score text against regex patterns."""
        score = 0.0
        matched = []

        for pattern, weight in patterns:
            matches = pattern.findall(text)
            if matches:
                score += weight * len(matches)
                matched.extend(matches)

        return score, matched

    def _score_tokens_and_lemmas(self, tokens: List[str], lemmas: List[str],
                                  token_set: Set[str], lemma_set: Set[str],
                                  weight: float = 1.0) -> Tuple[float, List[str]]:
        """Score by matching both tokens and lemmas."""
        score = 0.0
        matched = []

        # Match original tokens (higher weight - exact match)
        for token in tokens:
            if token in token_set:
                score += weight * 1.2  # Boost for exact token match
                if token not in matched:
                    matched.append(token)

        # Match lemmas (standard weight)
        for lemma in lemmas:
            if lemma in lemma_set:
                score += weight
                if lemma not in matched:
                    matched.append(f"[lemma:{lemma}]")

        return score, matched

    def classify(self, effect: str, recommendation: str = "") -> SeverityResult:
        """
        Classify the severity of a drug interaction.

        IMPROVED: Uses both pattern matching AND token/lemma matching.
        NOW WITH NEGATION DETECTION.
        """
        text = f"{effect} {recommendation}".strip()

        if not text:
            return SeverityResult(
                severity=Severity.UNKNOWN,
                confidence=0.0,
                matched_terms=[],
                linguistic_features={},
                reasoning="No text provided for analysis"
            )

        # Process with spaCy
        doc = self.nlp(text)

        # Extract tokens and lemmas
        tokens = [token.text.lower() for token in doc if not token.is_punct and not token.is_space]
        lemmas = [token.lemma_.lower() for token in doc if not token.is_punct and not token.is_space]

        # Check for intensifiers/diminishers
        has_intensifier = any(t in self.intensifiers for t in tokens)
        has_diminisher = any(t in self.diminishers for t in tokens)

        # NEGATION DETECTION - check for negated severity indicators
        negation_result = self._detect_negation(doc, text)

        # Score each severity level using BOTH patterns AND tokens/lemmas
        scores = {sev: 0.0 for sev in Severity if sev != Severity.UNKNOWN}
        all_matched = {sev: [] for sev in Severity if sev != Severity.UNKNOWN}

        # 1. Score with regex patterns (highest priority for phrases)
        pattern_score, pattern_matched = self._score_patterns(text, self.contraindicated_patterns)
        scores[Severity.CONTRAINDICATED] += pattern_score * 1.5  # Boost pattern matches
        all_matched[Severity.CONTRAINDICATED].extend(pattern_matched)

        pattern_score, pattern_matched = self._score_patterns(text, self.severe_patterns)
        scores[Severity.SEVERE] += pattern_score
        all_matched[Severity.SEVERE].extend(pattern_matched)

        pattern_score, pattern_matched = self._score_patterns(text, self.moderate_patterns)
        scores[Severity.MODERATE] += pattern_score
        all_matched[Severity.MODERATE].extend(pattern_matched)

        pattern_score, pattern_matched = self._score_patterns(text, self.mild_patterns)
        scores[Severity.MILD] += pattern_score
        all_matched[Severity.MILD].extend(pattern_matched)

        # 2. Score with token/lemma matching
        token_score, token_matched = self._score_tokens_and_lemmas(
            tokens, lemmas, self.contraindicated_tokens, self.contraindicated_lemmas, 1.5)
        scores[Severity.CONTRAINDICATED] += token_score
        all_matched[Severity.CONTRAINDICATED].extend(token_matched)

        token_score, token_matched = self._score_tokens_and_lemmas(
            tokens, lemmas, self.severe_tokens, self.severe_lemmas, 1.0)
        scores[Severity.SEVERE] += token_score
        all_matched[Severity.SEVERE].extend(token_matched)

        token_score, token_matched = self._score_tokens_and_lemmas(
            tokens, lemmas, self.moderate_tokens, self.moderate_lemmas, 0.8)
        scores[Severity.MODERATE] += token_score
        all_matched[Severity.MODERATE].extend(token_matched)

        token_score, token_matched = self._score_tokens_and_lemmas(
            tokens, lemmas, self.mild_tokens, self.mild_lemmas, 0.7)
        scores[Severity.MILD] += token_score
        all_matched[Severity.MILD].extend(token_matched)

        # 3. Apply modifiers
        if has_intensifier:
            scores[Severity.SEVERE] *= 1.3
            scores[Severity.CONTRAINDICATED] *= 1.2
        if has_diminisher:
            scores[Severity.SEVERE] *= 0.7
            scores[Severity.MODERATE] *= 0.8

        # 4. Apply NEGATION results
        if negation_result['has_negation_mild']:
            # Negation indicates MILD severity - boost mild, reduce others
            scores[Severity.MILD] += negation_result['negation_score_mild']
            all_matched[Severity.MILD].extend(negation_result['negated_terms'])
            # Reduce higher severity scores when negation indicates mild
            scores[Severity.SEVERE] *= 0.3
            scores[Severity.MODERATE] *= 0.5
            # Only reduce contraindicated if no explicit contraindication pattern
            if scores[Severity.CONTRAINDICATED] < 2.0:
                scores[Severity.CONTRAINDICATED] *= 0.3

        if negation_result['has_negation_contraindicated']:
            # Negation indicates CONTRAINDICATED (e.g., "no administrar conjuntamente")
            scores[Severity.CONTRAINDICATED] += negation_result['negation_score_contraindicated']
            all_matched[Severity.CONTRAINDICATED].extend(negation_result['negated_terms'])

        # 5. Determine best severity (priority order)
        if not any(scores.values()):
            return SeverityResult(
                severity=Severity.UNKNOWN,
                confidence=0.3,
                matched_terms=[],
                linguistic_features={'tokens': len(tokens), 'lemmas': len(lemmas)},
                reasoning="No severity indicators found in text"
            )

        # Priority: CONTRAINDICATED > SEVERE > MODERATE > MILD
        # But if negation_mild is strong, prefer MILD
        priority_order = [Severity.CONTRAINDICATED, Severity.SEVERE, Severity.MODERATE, Severity.MILD]

        # If strong negation indicates mild, prioritize MILD
        if negation_result['has_negation_mild'] and negation_result['negation_score_mild'] >= 2.0:
            best_severity = Severity.MILD
        # If CONTRAINDICATED has ANY significant score, use it (explicit clinical recommendation)
        elif scores[Severity.CONTRAINDICATED] >= 1.5:
            best_severity = Severity.CONTRAINDICATED
        else:
            # Otherwise, find highest score
            max_score = max(scores.values())
            best_severity = Severity.UNKNOWN

            for sev in priority_order:
                if scores[sev] > 0 and scores[sev] >= max_score * 0.7:
                    best_severity = sev
                    break

            if best_severity == Severity.UNKNOWN:
                best_severity = max(scores, key=scores.get)

        # Calculate confidence
        total_score = sum(scores.values())
        if total_score > 0:
            confidence = min(0.98, 0.5 + (scores[best_severity] / total_score) * 0.4)
            # Boost for multiple matches
            if len(all_matched[best_severity]) > 2:
                confidence = min(0.99, confidence + 0.1)
            # Boost confidence if negation clearly indicates the result
            if negation_result['has_negation_mild'] and best_severity == Severity.MILD:
                confidence = min(0.99, confidence + 0.15)
        else:
            confidence = 0.3

        # Remove duplicates from matched terms
        unique_matched = list(dict.fromkeys(all_matched[best_severity]))

        # Build reasoning
        reasoning_parts = [f"spaCy+patterns: matched {len(unique_matched)} {best_severity.value} indicators"]
        if negation_result['has_negation_mild']:
            reasoning_parts.append(f"negation detected (mild): {negation_result['negated_terms'][:2]}")
        if negation_result['has_negation_contraindicated']:
            reasoning_parts.append(f"negation detected (contraindicated): {negation_result['negated_terms'][:2]}")

        return SeverityResult(
            severity=best_severity,
            confidence=confidence,
            matched_terms=unique_matched,
            linguistic_features={
                'tokens_analyzed': len(tokens),
                'has_intensifier': has_intensifier,
                'has_diminisher': has_diminisher,
                'has_negation_mild': negation_result['has_negation_mild'],
                'has_negation_contraindicated': negation_result['has_negation_contraindicated'],
                'negation_score_mild': negation_result['negation_score_mild'],
                'scores': {k.value: round(v, 2) for k, v in scores.items()},
            },
            reasoning="; ".join(reasoning_parts)
        )

    def classify_batch(self, interactions: List[Dict]) -> List[SeverityResult]:
        """Classify multiple interactions."""
        results = []
        for interaction in interactions:
            effect = interaction.get('effect', interaction.get('efecto', ''))
            recommendation = interaction.get('recommendation', interaction.get('recomendacion', ''))
            results.append(self.classify(effect, recommendation))
        return results
