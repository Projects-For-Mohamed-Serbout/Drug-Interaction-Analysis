"""
Mechanism Extractor using spaCy and NLTK - IMPROVED VERSION.

This implementation extracts pharmacological mechanisms from text using:
- spaCy for NER-like extraction of enzymes, transporters, receptors
- NLTK for additional text processing
- Regex patterns for comprehensive CYP/transporter detection
- Dependency parsing to understand relationships
- BOTH token and lemma matching for comprehensive coverage
"""

import spacy
import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MechanismCategory(Enum):
    """Pharmacological mechanism categories."""
    PHARMACOKINETIC = "pharmacokinetic"      # ADME effects
    PHARMACODYNAMIC = "pharmacodynamic"       # Receptor/effect level
    MIXED = "mixed"                           # Both PK and PD
    UNKNOWN = "unknown"


class PKSubtype(Enum):
    """Pharmacokinetic subtypes."""
    ABSORPTION = "absorption"
    DISTRIBUTION = "distribution"
    METABOLISM_CYP = "metabolism_cyp"
    METABOLISM_OTHER = "metabolism_other"
    EXCRETION = "excretion"
    TRANSPORTER = "transporter"


class PDSubtype(Enum):
    """Pharmacodynamic subtypes."""
    ADDITIVE = "additive"
    SYNERGISTIC = "synergistic"
    ANTAGONISTIC = "antagonistic"
    RECEPTOR_COMPETITION = "receptor_competition"
    ELECTROPHYSIOLOGICAL = "electrophysiological"


@dataclass
class MechanismResult:
    """Result of mechanism extraction."""
    category: MechanismCategory
    pk_subtypes: List[PKSubtype] = field(default_factory=list)
    pd_subtypes: List[PDSubtype] = field(default_factory=list)
    enzymes: List[str] = field(default_factory=list)
    transporters: List[str] = field(default_factory=list)
    receptors: List[str] = field(default_factory=list)
    confidence: float = 0.0
    extracted_entities: Dict = field(default_factory=dict)
    reasoning: str = ""


class MechanismExtractorSpacy:
    """
    Extracts pharmacological mechanisms using spaCy.

    IMPROVED VERSION - Key changes:
    1. Comprehensive CYP enzyme patterns including all major CYPs
    2. Better transporter protein identification (P-gp, OATPs, etc.)
    3. Enhanced receptor identification
    4. Both token AND lemma matching
    5. Regex phrase patterns for mechanism indicators
    """

    def __init__(self, model_name: str = "es_core_news_md"):
        """Initialize the spaCy-based mechanism extractor."""
        self.model_name = model_name
        self._load_model()
        self._init_entity_patterns()
        self._init_mechanism_lexicons()
        self._init_mechanism_phrase_patterns()

    def _load_model(self):
        """Load spaCy model."""
        try:
            self.nlp = spacy.load(self.model_name)
            logger.info(f"Loaded spaCy model: {self.model_name}")
        except OSError:
            logger.warning(f"Model {self.model_name} not found, downloading...")
            spacy.cli.download(self.model_name)
            self.nlp = spacy.load(self.model_name)

        # Add custom entity ruler for pharmacological entities
        self._add_entity_ruler()

    def _add_entity_ruler(self):
        """Add custom entity patterns for pharmacological terms."""
        # Check if entity_ruler already exists
        if "entity_ruler" not in self.nlp.pipe_names:
            ruler = self.nlp.add_pipe("entity_ruler", before="ner")

            # CYP enzyme patterns - comprehensive
            cyp_patterns = [
                {"label": "CYP_ENZYME", "pattern": [{"TEXT": {"REGEX": r"CYP\d+[A-Z]\d*"}}]},
                {"label": "CYP_ENZYME", "pattern": [{"LOWER": "cyp"}, {"TEXT": {"REGEX": r"\d+[A-Za-z]\d*"}}]},
                {"label": "CYP_ENZYME", "pattern": [{"LOWER": "citocromo"}, {"LOWER": "p450"}]},
                {"label": "CYP_ENZYME", "pattern": [{"LOWER": "citocromo"}, {"TEXT": {"REGEX": r"CYP\d+"}}]},
                {"label": "CYP_ENZYME", "pattern": [{"LOWER": "cyp3a4"}]},
                {"label": "CYP_ENZYME", "pattern": [{"LOWER": "cyp2d6"}]},
                {"label": "CYP_ENZYME", "pattern": [{"LOWER": "cyp2c9"}]},
                {"label": "CYP_ENZYME", "pattern": [{"LOWER": "cyp2c19"}]},
                {"label": "CYP_ENZYME", "pattern": [{"LOWER": "cyp1a2"}]},
            ]

            # Transporter patterns - comprehensive
            transporter_patterns = [
                {"label": "TRANSPORTER", "pattern": [{"LOWER": "p-gp"}]},
                {"label": "TRANSPORTER", "pattern": [{"LOWER": "p-glicoproteina"}]},
                {"label": "TRANSPORTER", "pattern": [{"LOWER": "p-glicoproteína"}]},
                {"label": "TRANSPORTER", "pattern": [{"LOWER": "glicoproteina"}, {"LOWER": "p"}]},
                {"label": "TRANSPORTER", "pattern": [{"LOWER": "glicoproteína"}, {"LOWER": "p"}]},
                {"label": "TRANSPORTER", "pattern": [{"TEXT": {"REGEX": r"OAT[P]?\d*[A-Z]*\d*"}}]},
                {"label": "TRANSPORTER", "pattern": [{"TEXT": {"REGEX": r"OCT\d*"}}]},
                {"label": "TRANSPORTER", "pattern": [{"TEXT": {"REGEX": r"BCRP"}}]},
                {"label": "TRANSPORTER", "pattern": [{"TEXT": {"REGEX": r"MRP\d*"}}]},
                {"label": "TRANSPORTER", "pattern": [{"LOWER": "bomba"}, {"LOWER": "de"}, {"LOWER": "eflujo"}]},
                {"label": "TRANSPORTER", "pattern": [{"LOWER": "transportador"}]},
            ]

            # Receptor patterns - comprehensive
            receptor_patterns = [
                {"label": "RECEPTOR", "pattern": [{"LOWER": "receptor"}]},
                {"label": "RECEPTOR", "pattern": [{"LOWER": "receptores"}]},
                {"label": "RECEPTOR", "pattern": [{"TEXT": {"REGEX": r"5-?HT\d*"}}]},
                {"label": "RECEPTOR", "pattern": [{"LOWER": "gaba"}]},
                {"label": "RECEPTOR", "pattern": [{"LOWER": "nmda"}]},
                {"label": "RECEPTOR", "pattern": [{"LOWER": "dopamina"}]},
                {"label": "RECEPTOR", "pattern": [{"LOWER": "dopaminérgico"}]},
                {"label": "RECEPTOR", "pattern": [{"LOWER": "dopaminergico"}]},
                {"label": "RECEPTOR", "pattern": [{"LOWER": "adrenérgico"}]},
                {"label": "RECEPTOR", "pattern": [{"LOWER": "adrenergico"}]},
                {"label": "RECEPTOR", "pattern": [{"LOWER": "colinérgico"}]},
                {"label": "RECEPTOR", "pattern": [{"LOWER": "colinergico"}]},
                {"label": "RECEPTOR", "pattern": [{"LOWER": "histamina"}]},
                {"label": "RECEPTOR", "pattern": [{"LOWER": "opioide"}]},
                {"label": "RECEPTOR", "pattern": [{"LOWER": "muscarínico"}]},
                {"label": "RECEPTOR", "pattern": [{"LOWER": "muscarinico"}]},
                {"label": "RECEPTOR", "pattern": [{"LOWER": "nicotínico"}]},
                {"label": "RECEPTOR", "pattern": [{"LOWER": "nicotinico"}]},
                {"label": "RECEPTOR", "pattern": [{"LOWER": "serotonina"}]},
            ]

            all_patterns = cyp_patterns + transporter_patterns + receptor_patterns
            ruler.add_patterns(all_patterns)

    def _init_entity_patterns(self):
        """Initialize regex patterns for entity extraction - IMPROVED."""

        # CYP450 enzyme patterns - comprehensive
        self.cyp_pattern = re.compile(
            r'\b(CYP\s*\d+[A-Z]\d*|citocromo\s*P?\s*450|CYP450|'
            r'CYP3A4|CYP3A5|CYP2D6|CYP2C9|CYP2C19|CYP1A2|CYP2B6|CYP2C8|CYP2E1|CYP2A6)\b',
            re.IGNORECASE
        )

        # Specific CYP enzymes - comprehensive list
        self.specific_cyps = {
            'cyp3a4', 'cyp3a5', 'cyp3a7', 'cyp2d6', 'cyp2c9', 'cyp2c19', 'cyp2c8',
            'cyp1a2', 'cyp1a1', 'cyp1b1', 'cyp2b6', 'cyp2e1', 'cyp2a6',
        }

        # Transporter patterns - comprehensive
        self.transporter_pattern = re.compile(
            r'\b(P-?gp|P-?glicoprote[ií]na|glicoprote[ií]na\s*P|'
            r'OATP\d*[A-Z]*\d*|OAT\d+|OCT\d*|BCRP|MRP\d*|'
            r'transportador(?:es)?|bomba\s+de\s+eflujo|'
            r'MDR1|ABCB1|SLCO\d+[A-Z]\d*)\b',
            re.IGNORECASE
        )

        # Receptor patterns - comprehensive
        self.receptor_pattern = re.compile(
            r'\b(receptor(?:es)?|5-?HT\d*[A-Z]?|GABA[A-B]?|NMDA|'
            r'dopamin[ae]|dopamin[eé]rgico|'
            r'adren[eé]rgico|alfa\d*|beta\d*|'
            r'colin[eé]rgico|anticolinergic|'
            r'histamin[ae]|H\d|opioide|mu|kappa|delta|'
            r'muscar[ií]nico|M\d|nicot[ií]nico|'
            r'serotonin[ae]|5HT|serotoninergic)\b',
            re.IGNORECASE
        )

    def _init_mechanism_phrase_patterns(self):
        """Initialize regex patterns for mechanism phrase detection."""

        # PHARMACOKINETIC phrase patterns
        self.pk_patterns = [
            # Metabolism
            (re.compile(r'\bmetabolismo\s+hep[aá]tico\b', re.IGNORECASE), 'metabolism', 2.0),
            (re.compile(r'\binducci[oó]n\s+(?:del?\s+)?(?:metabolismo|CYP)\b', re.IGNORECASE), 'metabolism', 2.5),
            (re.compile(r'\binhibici[oó]n\s+(?:del?\s+)?(?:metabolismo|CYP)\b', re.IGNORECASE), 'metabolism', 2.5),
            (re.compile(r'\bmediado\s+por\s+CYP', re.IGNORECASE), 'metabolism', 2.0),
            (re.compile(r'\bv[ií]a\s+CYP', re.IGNORECASE), 'metabolism', 1.5),
            (re.compile(r'\bsustrato\s+(?:del?\s+)?CYP', re.IGNORECASE), 'metabolism', 2.0),
            (re.compile(r'\binductor\s+(?:del?\s+)?CYP', re.IGNORECASE), 'metabolism', 2.5),
            (re.compile(r'\binhibidor\s+(?:del?\s+)?CYP', re.IGNORECASE), 'metabolism', 2.5),
            (re.compile(r'\bcitocromo\s+P\s*450', re.IGNORECASE), 'metabolism', 2.0),
            # Absorption
            (re.compile(r'\babsorci[oó]n\s+(?:intestinal|oral|g[aá]strica)\b', re.IGNORECASE), 'absorption', 1.8),
            (re.compile(r'\bdisminuye\s+(?:la\s+)?absorci[oó]n\b', re.IGNORECASE), 'absorption', 2.0),
            (re.compile(r'\bbiodisponibilidad\b', re.IGNORECASE), 'absorption', 1.5),
            # Excretion
            (re.compile(r'\beliminaci[oó]n\s+renal\b', re.IGNORECASE), 'excretion', 1.8),
            (re.compile(r'\baclaramiento\s+(?:renal|hep[aá]tico)\b', re.IGNORECASE), 'excretion', 1.8),
            (re.compile(r'\bexcreci[oó]n\b', re.IGNORECASE), 'excretion', 1.5),
            # Transporter
            (re.compile(r'\btransporte\s+(?:activo|de\s+eflujo)\b', re.IGNORECASE), 'transporter', 1.8),
            (re.compile(r'\bP-?(?:gp|glicoprote[ií]na)\b', re.IGNORECASE), 'transporter', 2.0),
            (re.compile(r'\bbomba\s+de\s+eflujo\b', re.IGNORECASE), 'transporter', 2.0),
        ]

        # PHARMACODYNAMIC phrase patterns
        self.pd_patterns = [
            # Additive
            (re.compile(r'\befecto\s+aditivo\b', re.IGNORECASE), 'additive', 2.0),
            (re.compile(r'\bsuma\s+de\s+efectos\b', re.IGNORECASE), 'additive', 1.8),
            # Synergistic
            (re.compile(r'\befecto\s+sin[eé]rgico\b', re.IGNORECASE), 'synergistic', 2.0),
            (re.compile(r'\bsinergia\b', re.IGNORECASE), 'synergistic', 1.8),
            (re.compile(r'\bpotenciaci[oó]n\s+(?:del?\s+)?efecto\b', re.IGNORECASE), 'synergistic', 2.0),
            # Antagonistic
            (re.compile(r'\bantagonismo\b', re.IGNORECASE), 'antagonistic', 2.0),
            (re.compile(r'\bbloqueo\s+(?:del?\s+)?receptor\b', re.IGNORECASE), 'antagonistic', 1.8),
            # Receptor
            (re.compile(r'\bcompetici[oó]n\s+(?:por\s+)?receptor(?:es)?\b', re.IGNORECASE), 'receptor', 2.0),
            (re.compile(r'\bafinidad\s+(?:por\s+)?receptor(?:es)?\b', re.IGNORECASE), 'receptor', 1.8),
            (re.compile(r'\bdesplazamiento\s+(?:del?\s+)?receptor\b', re.IGNORECASE), 'receptor', 1.8),
            # Electrophysiological
            (re.compile(r'\bprolongaci[oó]n\s+(?:del?\s+)?(?:intervalo\s+)?QT\b', re.IGNORECASE), 'electrophysiological', 2.5),
            (re.compile(r'\bintervalo\s+QT\b', re.IGNORECASE), 'electrophysiological', 2.0),
            (re.compile(r'\brepolarizaci[oó]n\b', re.IGNORECASE), 'electrophysiological', 1.5),
            (re.compile(r'\btorsade[s]?\s+de\s+pointes\b', re.IGNORECASE), 'electrophysiological', 2.5),
        ]

    def _init_mechanism_lexicons(self):
        """Initialize lexicons for mechanism classification - IMPROVED with tokens AND lemmas."""

        # Pharmacokinetic indicators - tokens
        self.pk_absorption_tokens = {
            'absorción', 'absorcion', 'biodisponibilidad', 'absorber',
            'intestinal', 'gástrico', 'gastrico', 'oral', 'enteral',
        }
        self.pk_absorption_lemmas = {'absorción', 'biodisponibilidad', 'absorber'}

        self.pk_distribution_tokens = {
            'distribución', 'distribucion', 'proteínas', 'proteinas', 'albúmina', 'albumina',
            'volumen', 'barrera', 'hematoencefálica', 'hematoencefalica',
            'tejido', 'tejidos', 'plasma', 'plasmático', 'plasmatico',
        }
        self.pk_distribution_lemmas = {'distribución', 'proteína', 'albúmina', 'tejido', 'plasma'}

        self.pk_metabolism_tokens = {
            'metabolismo', 'metabolizar', 'metabolito', 'metabolitos',
            'citocromo', 'cyp', 'biotransformación', 'biotransformacion',
            'hidroxilación', 'hidroxilacion', 'oxidación', 'oxidacion',
            'glucuronidación', 'glucuronidacion', 'conjugación', 'conjugacion',
            'inductor', 'inductores', 'inhibidor', 'inhibidores',
            'inducción', 'induccion', 'inhibición', 'inhibicion',
            'hepático', 'hepatico',
        }
        self.pk_metabolism_lemmas = {
            'metabolismo', 'metabolizar', 'metabolito', 'citocromo',
            'inductor', 'inhibidor', 'hepático',
        }

        self.pk_excretion_tokens = {
            'excreción', 'excrecion', 'eliminación', 'eliminacion',
            'aclaramiento', 'renal', 'renales', 'hepático', 'hepatico',
            'biliar', 'biliares', 'vida', 'media', 'semivida',
        }
        self.pk_excretion_lemmas = {'excreción', 'eliminación', 'aclaramiento', 'renal'}

        self.pk_transporter_tokens = {
            'transportador', 'transportadores', 'p-gp', 'pgp',
            'glicoproteína', 'glicoproteina', 'eflujo', 'captación', 'captacion',
            'oatp', 'oct', 'bcrp', 'mrp', 'mdr1', 'abcb1',
        }
        self.pk_transporter_lemmas = {'transportador', 'glicoproteína', 'eflujo'}

        # Pharmacodynamic indicators - tokens
        self.pd_additive_tokens = {
            'aditivo', 'aditivos', 'sumar', 'acumulativo', 'acumulativos',
        }
        self.pd_additive_lemmas = {'aditivo', 'sumar', 'acumulativo'}

        self.pd_synergistic_tokens = {
            'sinérgico', 'sinergico', 'sinergia', 'sinergismo',
            'potenciación', 'potenciacion', 'potenciar', 'potencia',
        }
        self.pd_synergistic_lemmas = {'sinérgico', 'sinergia', 'potenciación', 'potenciar'}

        self.pd_antagonistic_tokens = {
            'antagonista', 'antagonistas', 'antagonismo', 'antagonizar',
            'bloquear', 'bloqueo', 'inhibir', 'inhibición', 'inhibicion',
        }
        self.pd_antagonistic_lemmas = {'antagonista', 'antagonismo', 'bloquear', 'inhibir'}

        self.pd_receptor_tokens = {
            'receptor', 'receptores', 'unión', 'union', 'afinidad',
            'agonista', 'agonistas', 'competición', 'competicion',
            'desplazamiento',
        }
        self.pd_receptor_lemmas = {'receptor', 'unión', 'afinidad', 'agonista'}

        self.pd_electrophysiological_tokens = {
            'qt', 'electrocardiograma', 'ecg', 'intervalo',
            'repolarización', 'repolarizacion', 'despolarización', 'despolarizacion',
            'conducción', 'conduccion', 'arritmia', 'arritmias',
            'torsade', 'pointes',
        }
        self.pd_electrophysiological_lemmas = {
            'qt', 'electrocardiograma', 'intervalo', 'repolarización', 'arritmia',
        }

    def _score_patterns(self, text: str, patterns: List[Tuple]) -> Dict[str, float]:
        """Score text against mechanism patterns."""
        scores = {}
        for pattern, category, weight in patterns:
            matches = pattern.findall(text)
            if matches:
                if category not in scores:
                    scores[category] = 0
                scores[category] += weight * len(matches)
        return scores

    def _extract_cyp_enzymes(self, text: str, doc) -> List[str]:
        """Extract CYP enzyme mentions from text - IMPROVED."""
        enzymes = set()

        # Use spaCy entities
        for ent in doc.ents:
            if ent.label_ == "CYP_ENZYME":
                enzymes.add(ent.text.upper())

        # Use comprehensive regex pattern
        matches = self.cyp_pattern.findall(text)
        for match in matches:
            normalized = match.upper().replace(" ", "")
            enzymes.add(normalized)

        # Check for specific CYP mentions in text (case insensitive)
        text_lower = text.lower()
        for cyp in self.specific_cyps:
            if cyp in text_lower:
                enzymes.add(cyp.upper())

        # Also check tokens
        for token in doc:
            token_lower = token.text.lower()
            for cyp in self.specific_cyps:
                if cyp in token_lower:
                    enzymes.add(cyp.upper())

        return list(enzymes)

    def _extract_transporters(self, text: str, doc) -> List[str]:
        """Extract transporter protein mentions - IMPROVED."""
        transporters = set()

        # Use spaCy entities
        for ent in doc.ents:
            if ent.label_ == "TRANSPORTER":
                transporters.add(ent.text)

        # Use comprehensive regex pattern
        matches = self.transporter_pattern.findall(text)
        for match in matches:
            transporters.add(match)

        # Check for common transporter tokens
        text_lower = text.lower()
        common_transporters = ['p-gp', 'pgp', 'p-glicoproteína', 'oatp', 'bcrp', 'mrp']
        for trans in common_transporters:
            if trans in text_lower:
                transporters.add(trans.upper())

        return list(transporters)

    def _extract_receptors(self, text: str, doc) -> List[str]:
        """Extract receptor mentions - IMPROVED."""
        receptors = set()

        # Use spaCy entities
        for ent in doc.ents:
            if ent.label_ == "RECEPTOR":
                receptors.add(ent.text)

        # Use comprehensive regex pattern
        matches = self.receptor_pattern.findall(text)
        for match in matches:
            receptors.add(match)

        return list(receptors)

    def _classify_mechanism(self, tokens: List[str], lemmas: List[str],
                           enzymes: List[str], transporters: List[str],
                           receptors: List[str], pattern_scores: Dict[str, float]) -> Tuple:
        """
        Classify the mechanism category and subtypes - IMPROVED.

        Returns (category, pk_subtypes, pd_subtypes)
        """
        pk_score = 0.0
        pd_score = 0.0
        pk_subtypes = []
        pd_subtypes = []

        token_set = set(tokens)
        lemma_set = set(lemmas)

        # Check PK indicators - using both tokens and lemmas
        absorption_match = (
            (token_set & self.pk_absorption_tokens) or
            (lemma_set & self.pk_absorption_lemmas) or
            pattern_scores.get('absorption', 0) > 0
        )
        if absorption_match:
            pk_score += 1 + pattern_scores.get('absorption', 0)
            pk_subtypes.append(PKSubtype.ABSORPTION)

        distribution_match = (
            (token_set & self.pk_distribution_tokens) or
            (lemma_set & self.pk_distribution_lemmas)
        )
        if distribution_match:
            pk_score += 1
            pk_subtypes.append(PKSubtype.DISTRIBUTION)

        metabolism_match = (
            (token_set & self.pk_metabolism_tokens) or
            (lemma_set & self.pk_metabolism_lemmas) or
            enzymes or
            pattern_scores.get('metabolism', 0) > 0
        )
        if metabolism_match:
            pk_score += 2 + pattern_scores.get('metabolism', 0)  # Higher weight for metabolism
            if enzymes:
                pk_subtypes.append(PKSubtype.METABOLISM_CYP)
            else:
                pk_subtypes.append(PKSubtype.METABOLISM_OTHER)

        excretion_match = (
            (token_set & self.pk_excretion_tokens) or
            (lemma_set & self.pk_excretion_lemmas) or
            pattern_scores.get('excretion', 0) > 0
        )
        if excretion_match:
            pk_score += 1 + pattern_scores.get('excretion', 0)
            pk_subtypes.append(PKSubtype.EXCRETION)

        transporter_match = (
            (token_set & self.pk_transporter_tokens) or
            (lemma_set & self.pk_transporter_lemmas) or
            transporters or
            pattern_scores.get('transporter', 0) > 0
        )
        if transporter_match:
            pk_score += 1.5 + pattern_scores.get('transporter', 0)
            pk_subtypes.append(PKSubtype.TRANSPORTER)

        # Check PD indicators
        additive_match = (
            (token_set & self.pd_additive_tokens) or
            (lemma_set & self.pd_additive_lemmas) or
            pattern_scores.get('additive', 0) > 0
        )
        if additive_match:
            pd_score += 1 + pattern_scores.get('additive', 0)
            pd_subtypes.append(PDSubtype.ADDITIVE)

        synergistic_match = (
            (token_set & self.pd_synergistic_tokens) or
            (lemma_set & self.pd_synergistic_lemmas) or
            pattern_scores.get('synergistic', 0) > 0
        )
        if synergistic_match:
            pd_score += 1 + pattern_scores.get('synergistic', 0)
            pd_subtypes.append(PDSubtype.SYNERGISTIC)

        antagonistic_match = (
            (token_set & self.pd_antagonistic_tokens) or
            (lemma_set & self.pd_antagonistic_lemmas) or
            pattern_scores.get('antagonistic', 0) > 0
        )
        if antagonistic_match:
            pd_score += 1 + pattern_scores.get('antagonistic', 0)
            pd_subtypes.append(PDSubtype.ANTAGONISTIC)

        receptor_match = (
            (token_set & self.pd_receptor_tokens) or
            (lemma_set & self.pd_receptor_lemmas) or
            receptors or
            pattern_scores.get('receptor', 0) > 0
        )
        if receptor_match:
            pd_score += 1.5 + pattern_scores.get('receptor', 0)
            pd_subtypes.append(PDSubtype.RECEPTOR_COMPETITION)

        electrophysiological_match = (
            (token_set & self.pd_electrophysiological_tokens) or
            (lemma_set & self.pd_electrophysiological_lemmas) or
            pattern_scores.get('electrophysiological', 0) > 0
        )
        if electrophysiological_match:
            pd_score += 1 + pattern_scores.get('electrophysiological', 0)
            pd_subtypes.append(PDSubtype.ELECTROPHYSIOLOGICAL)

        # Determine category
        if pk_score > 0 and pd_score > 0:
            category = MechanismCategory.MIXED
        elif pk_score > pd_score:
            category = MechanismCategory.PHARMACOKINETIC
        elif pd_score > pk_score:
            category = MechanismCategory.PHARMACODYNAMIC
        else:
            category = MechanismCategory.UNKNOWN

        return category, list(set(pk_subtypes)), list(set(pd_subtypes))

    def extract(self, effect: str, recommendation: str = "") -> MechanismResult:
        """
        Extract pharmacological mechanism from text using spaCy - IMPROVED.

        Args:
            effect: The effect description (Spanish text)
            recommendation: The recommendation text (Spanish text)

        Returns:
            MechanismResult with mechanism details
        """
        text = f"{effect} {recommendation}".strip()

        if not text:
            return MechanismResult(
                category=MechanismCategory.UNKNOWN,
                confidence=0.0,
                reasoning="No text provided for analysis"
            )

        # Process with spaCy
        doc = self.nlp(text)

        # Extract tokens and lemmas
        tokens = [token.text.lower() for token in doc if not token.is_punct and not token.is_space]
        lemmas = [token.lemma_.lower() for token in doc if not token.is_punct and not token.is_space]

        # Score phrase patterns
        pk_pattern_scores = self._score_patterns(text, self.pk_patterns)
        pd_pattern_scores = self._score_patterns(text, self.pd_patterns)
        all_pattern_scores = {**pk_pattern_scores, **pd_pattern_scores}

        # Extract entities
        enzymes = self._extract_cyp_enzymes(text, doc)
        transporters = self._extract_transporters(text, doc)
        receptors = self._extract_receptors(text, doc)

        # Classify mechanism
        category, pk_subtypes, pd_subtypes = self._classify_mechanism(
            tokens, lemmas, enzymes, transporters, receptors, all_pattern_scores
        )

        # Calculate confidence
        entity_count = len(enzymes) + len(transporters) + len(receptors)
        subtype_count = len(pk_subtypes) + len(pd_subtypes)
        pattern_score_total = sum(all_pattern_scores.values())

        if category == MechanismCategory.UNKNOWN:
            confidence = 0.3
        else:
            confidence = min(0.98, 0.5 + (entity_count * 0.1) + (subtype_count * 0.08) + (pattern_score_total * 0.05))

        # Build reasoning
        reasoning_parts = []
        if enzymes:
            reasoning_parts.append(f"CYP enzymes: {', '.join(enzymes)}")
        if transporters:
            reasoning_parts.append(f"Transporters: {', '.join(transporters)}")
        if receptors:
            reasoning_parts.append(f"Receptors: {', '.join(receptors)}")
        if pk_subtypes:
            reasoning_parts.append(f"PK: {', '.join(s.value for s in pk_subtypes)}")
        if pd_subtypes:
            reasoning_parts.append(f"PD: {', '.join(s.value for s in pd_subtypes)}")

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No specific mechanism identified"

        return MechanismResult(
            category=category,
            pk_subtypes=pk_subtypes,
            pd_subtypes=pd_subtypes,
            enzymes=enzymes,
            transporters=transporters,
            receptors=receptors,
            confidence=confidence,
            extracted_entities={
                'enzymes': enzymes,
                'transporters': transporters,
                'receptors': receptors,
            },
            reasoning=reasoning
        )

    def extract_batch(self, interactions: List[Dict]) -> List[MechanismResult]:
        """
        Extract mechanisms from multiple interactions.

        Args:
            interactions: List of dicts with 'effect'/'efecto' and 'recommendation'/'recomendacion'

        Returns:
            List of MechanismResult objects
        """
        results = []

        for interaction in interactions:
            effect = interaction.get('effect', interaction.get('efecto', ''))
            recommendation = interaction.get('recommendation', interaction.get('recomendacion', ''))
            results.append(self.extract(effect, recommendation))

        return results
