"""
Mechanism Extractor for Drug Interactions.

Extracts and classifies the pharmacological mechanism
of drug interactions from Spanish clinical text.
"""
import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MechanismCategory(Enum):
    """Categories of drug interaction mechanisms."""
    PHARMACOKINETIC = "pharmacokinetic"    # Absorption, metabolism, excretion
    PHARMACODYNAMIC = "pharmacodynamic"    # Receptor-level interactions
    MIXED = "mixed"                        # Both PK and PD
    UNKNOWN = "unknown"                    # Cannot determine


class PKMechanism(Enum):
    """Pharmacokinetic mechanism subtypes."""
    ABSORPTION = "absorption"              # GI absorption changes
    DISTRIBUTION = "distribution"          # Protein binding, tissue distribution
    METABOLISM_CYP = "metabolism_cyp"      # Cytochrome P450 enzymes
    METABOLISM_OTHER = "metabolism_other"  # Other metabolic pathways
    EXCRETION = "excretion"                # Renal/biliary elimination
    TRANSPORTER = "transporter"            # Drug transporters (P-gp, etc.)


class PDMechanism(Enum):
    """Pharmacodynamic mechanism subtypes."""
    ADDITIVE = "additive"                  # Same effect, additive
    SYNERGISTIC = "synergistic"            # Enhanced combined effect
    ANTAGONISTIC = "antagonistic"          # Opposing effects
    RECEPTOR_COMPETITION = "receptor_competition"  # Same receptor target
    ELECTROPHYSIOLOGICAL = "electrophysiological"  # Ion channels, QT effects


@dataclass
class MechanismResult:
    """Result of mechanism extraction."""
    category: MechanismCategory
    pk_mechanisms: List[PKMechanism]
    pd_mechanisms: List[PDMechanism]
    enzymes_involved: List[str]
    transporters_involved: List[str]
    receptors_involved: List[str]
    confidence: float
    extracted_phrases: List[str]


class MechanismExtractor:
    """
    Extracts drug interaction mechanisms from Spanish pharmaceutical text.

    Identifies pharmacokinetic and pharmacodynamic mechanisms,
    including specific enzymes, transporters, and receptors involved.
    """

    def __init__(self):
        """Initialize the mechanism extractor."""
        self._init_patterns()

    def _init_patterns(self):
        """Initialize extraction patterns."""

        # Pharmacokinetic patterns
        self.pk_patterns = {
            PKMechanism.ABSORPTION: [
                (r'(?:disminuye?|reduce?|aumenta?|altera?)\s+(?:la\s+)?absorci[oó]n', 0.9),
                (r'absorci[oó]n\s+(?:intestinal|g[aá]strica|oral)', 0.85),
                (r'biodisponibilidad', 0.8),
                (r'vaciamiento\s+g[aá]strico', 0.8),
                (r'quelaci[oó]n', 0.85),
                (r'formaci[oó]n\s+de\s+complejos', 0.8),
                (r'pH\s+g[aá]strico', 0.75),
            ],

            PKMechanism.DISTRIBUTION: [
                (r'desplazamiento\s+(?:de\s+)?(?:la\s+)?uni[oó]n\s+a\s+prote[ií]nas', 0.9),
                (r'uni[oó]n\s+a\s+prote[ií]nas\s+plasm[aá]ticas', 0.85),
                (r'alb[uú]mina', 0.7),
                (r'volumen\s+de\s+distribuci[oó]n', 0.8),
                (r'barrera\s+hematoencef[aá]lica', 0.8),
            ],

            PKMechanism.METABOLISM_CYP: [
                (r'CYP\s*[123]\w*', 0.95),
                (r'citocromo\s+P\s*-?\s*450', 0.95),
                (r'CYP3A4', 0.95),
                (r'CYP2D6', 0.95),
                (r'CYP2C9', 0.95),
                (r'CYP2C19', 0.95),
                (r'CYP1A2', 0.95),
                (r'inh[ií]be?\s+(?:el\s+)?CYP', 0.95),
                (r'inductor?\s+(?:del?\s+)?CYP', 0.95),
                (r'inhibidor?\s+enzim[aá]tic[ao]', 0.85),
                (r'inducci[oó]n\s+enzim[aá]tica', 0.85),
            ],

            PKMechanism.METABOLISM_OTHER: [
                (r'glucuronidaci[oó]n', 0.9),
                (r'UGT', 0.9),
                (r'acetilaci[oó]n', 0.85),
                (r'metilaci[oó]n', 0.85),
                (r'conjugaci[oó]n', 0.8),
                (r'metabolismo\s+hep[aá]tico', 0.8),
                (r'primer\s+paso', 0.75),
                (r'MAO', 0.9),
                (r'monoaminooxidasa', 0.9),
            ],

            PKMechanism.EXCRETION: [
                (r'eliminaci[oó]n\s+renal', 0.9),
                (r'aclaramiento\s+renal', 0.9),
                (r'excreci[oó]n\s+(?:renal|biliar|tubular)', 0.9),
                (r'reabsorci[oó]n\s+tubular', 0.85),
                (r'secreci[oó]n\s+tubular', 0.85),
                (r'filtrado\s+glomerular', 0.8),
                (r'pH\s+urinario', 0.8),
                (r'competencia\s+(?:por\s+)?(?:la\s+)?excreci[oó]n', 0.85),
            ],

            PKMechanism.TRANSPORTER: [
                (r'P-?\s*glicoprote[ií]na', 0.95),
                (r'P-?\s*gp', 0.95),
                (r'OATP', 0.95),
                (r'OCT[12]?', 0.9),
                (r'OAT[123]?', 0.9),
                (r'BCRP', 0.9),
                (r'MRP[12]?', 0.9),
                (r'transportador(?:es)?\s+(?:de\s+)?membrana', 0.8),
                (r'eflujo', 0.75),
                (r'influx', 0.75),
            ],
        }

        # Pharmacodynamic patterns
        self.pd_patterns = {
            PDMechanism.ADDITIVE: [
                (r'efecto\s+aditivo', 0.95),
                (r'efectos?\s+aditivos?', 0.95),
                (r'sumaci[oó]n\s+de\s+efectos', 0.9),
                (r'ambos\s+(?:producen|causan)', 0.75),
                (r'potenciaci[oó]n\s+del\s+efecto', 0.8),
            ],

            PDMechanism.SYNERGISTIC: [
                (r'sinerg(?:ismo|ia)', 0.95),
                (r'sin[eé]rgic[ao]', 0.95),
                (r'potenciaci[oó]n', 0.8),
                (r'amplificaci[oó]n', 0.8),
                (r'supraditivo', 0.9),
            ],

            PDMechanism.ANTAGONISTIC: [
                (r'antagonismo', 0.95),
                (r'antagonista', 0.9),
                (r'efecto\s+opuesto', 0.85),
                (r'contrarresta', 0.8),
                (r'inhibe?\s+el\s+efecto', 0.8),
                (r'bloquea?\s+el\s+efecto', 0.8),
                (r'neutraliza', 0.75),
            ],

            PDMechanism.RECEPTOR_COMPETITION: [
                (r'competencia\s+(?:por\s+)?(?:el\s+)?receptor', 0.95),
                (r'mismo\s+receptor', 0.9),
                (r'receptor(?:es)?\s+\w+[eé]rgic[ao]s?', 0.85),
                (r'afinidad\s+(?:por\s+)?(?:el\s+)?receptor', 0.85),
                (r'desplazamiento\s+del\s+receptor', 0.85),
            ],

            PDMechanism.ELECTROPHYSIOLOGICAL: [
                (r'prolongaci[oó]n\s+(?:del\s+)?(?:intervalo\s+)?QT', 0.95),
                (r'intervalo\s+QT', 0.95),
                (r'QTc', 0.95),
                (r'canales?\s+(?:de\s+)?(?:potasio|sodio|calcio)', 0.9),
                (r'hERG', 0.95),
                (r'repolarizaci[oó]n', 0.85),
                (r'despolarizaci[oó]n', 0.85),
                (r'conducci[oó]n\s+card[ií]aca', 0.85),
            ],
        }

        # CYP enzyme patterns for extraction
        self.cyp_pattern = re.compile(r'CYP\s*([123]\w{1,3})', re.IGNORECASE)

        # Transporter patterns for extraction
        self.transporter_patterns = [
            re.compile(r'P-?\s*(?:glicoprote[ií]na|gp)', re.IGNORECASE),
            re.compile(r'OATP\s*\d*\w*', re.IGNORECASE),
            re.compile(r'OCT\s*[12]?', re.IGNORECASE),
            re.compile(r'OAT\s*[123]?', re.IGNORECASE),
            re.compile(r'BCRP', re.IGNORECASE),
            re.compile(r'MRP\s*[12]?', re.IGNORECASE),
        ]

        # Receptor patterns for extraction
        self.receptor_patterns = [
            (re.compile(r'receptor(?:es)?\s+(\w+[eé]rgic[ao]s?)', re.IGNORECASE), 1),
            (re.compile(r'(\w+[eé]rgic[ao]s?)\s+receptor(?:es)?', re.IGNORECASE), 1),
            (re.compile(r'receptor(?:es)?\s+de\s+(\w+)', re.IGNORECASE), 1),
        ]

        # Compile all patterns
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns."""
        self.compiled_pk = {
            mech: [(re.compile(p, re.IGNORECASE), w) for p, w in patterns]
            for mech, patterns in self.pk_patterns.items()
        }

        self.compiled_pd = {
            mech: [(re.compile(p, re.IGNORECASE), w) for p, w in patterns]
            for mech, patterns in self.pd_patterns.items()
        }

    def extract(self, effect: str, recommendation: str = "") -> MechanismResult:
        """
        Extract mechanism information from interaction text.

        Args:
            effect: The effect description (Spanish text)
            recommendation: The recommendation text (Spanish text)

        Returns:
            MechanismResult with extracted mechanism information
        """
        text = f"{effect} {recommendation}".strip()

        if not text:
            return MechanismResult(
                category=MechanismCategory.UNKNOWN,
                pk_mechanisms=[],
                pd_mechanisms=[],
                enzymes_involved=[],
                transporters_involved=[],
                receptors_involved=[],
                confidence=0.0,
                extracted_phrases=[]
            )

        # Extract PK mechanisms
        pk_results = self._extract_pk_mechanisms(text)
        pk_mechanisms = list(pk_results.keys())

        # Extract PD mechanisms
        pd_results = self._extract_pd_mechanisms(text)
        pd_mechanisms = list(pd_results.keys())

        # Extract specific entities
        enzymes = self._extract_enzymes(text)
        transporters = self._extract_transporters(text)
        receptors = self._extract_receptors(text)

        # Determine category
        has_pk = len(pk_mechanisms) > 0
        has_pd = len(pd_mechanisms) > 0

        if has_pk and has_pd:
            category = MechanismCategory.MIXED
        elif has_pk:
            category = MechanismCategory.PHARMACOKINETIC
        elif has_pd:
            category = MechanismCategory.PHARMACODYNAMIC
        else:
            category = MechanismCategory.UNKNOWN

        # Calculate confidence
        all_weights = []
        for mech, (matches, weight) in pk_results.items():
            all_weights.append(weight)
        for mech, (matches, weight) in pd_results.items():
            all_weights.append(weight)

        if all_weights:
            confidence = min(0.95, max(all_weights))
        else:
            confidence = 0.3

        # Collect extracted phrases
        phrases = []
        for mech, (matches, _) in pk_results.items():
            phrases.extend(matches)
        for mech, (matches, _) in pd_results.items():
            phrases.extend(matches)

        return MechanismResult(
            category=category,
            pk_mechanisms=pk_mechanisms,
            pd_mechanisms=pd_mechanisms,
            enzymes_involved=enzymes,
            transporters_involved=transporters,
            receptors_involved=receptors,
            confidence=confidence,
            extracted_phrases=list(set(phrases))[:10]  # Limit to 10
        )

    def _extract_pk_mechanisms(self, text: str) -> Dict[PKMechanism, tuple]:
        """Extract pharmacokinetic mechanisms."""
        results = {}

        for mech, patterns in self.compiled_pk.items():
            max_weight = 0.0
            all_matches = []

            for pattern, weight in patterns:
                matches = pattern.findall(text)
                if matches:
                    all_matches.extend(matches)
                    max_weight = max(max_weight, weight)

            if all_matches:
                results[mech] = (all_matches, max_weight)

        return results

    def _extract_pd_mechanisms(self, text: str) -> Dict[PDMechanism, tuple]:
        """Extract pharmacodynamic mechanisms."""
        results = {}

        for mech, patterns in self.compiled_pd.items():
            max_weight = 0.0
            all_matches = []

            for pattern, weight in patterns:
                matches = pattern.findall(text)
                if matches:
                    all_matches.extend(matches)
                    max_weight = max(max_weight, weight)

            if all_matches:
                results[mech] = (all_matches, max_weight)

        return results

    def _extract_enzymes(self, text: str) -> List[str]:
        """Extract CYP enzyme names."""
        enzymes: Set[str] = set()

        # Find CYP enzymes
        for match in self.cyp_pattern.finditer(text):
            enzyme = f"CYP{match.group(1).upper()}"
            enzymes.add(enzyme)

        # Also check for generic CYP mentions
        if re.search(r'citocromo\s+P\s*-?\s*450', text, re.IGNORECASE):
            if not enzymes:
                enzymes.add("CYP450")

        return sorted(list(enzymes))

    def _extract_transporters(self, text: str) -> List[str]:
        """Extract drug transporter names."""
        transporters: Set[str] = set()

        for pattern in self.transporter_patterns:
            for match in pattern.finditer(text):
                transporter = match.group(0).upper()
                # Normalize P-glycoprotein variations
                if 'GLICOPROTE' in transporter or transporter.startswith('P-G') or transporter == 'P-GP':
                    transporter = 'P-gp'
                transporters.add(transporter)

        return sorted(list(transporters))

    def _extract_receptors(self, text: str) -> List[str]:
        """Extract receptor names."""
        receptors: Set[str] = set()

        for pattern, group in self.receptor_patterns:
            for match in pattern.finditer(text):
                receptor = match.group(group).lower()
                # Normalize common receptor types
                if 'adren' in receptor:
                    receptors.add('adrenergic')
                elif 'colin' in receptor:
                    receptors.add('cholinergic')
                elif 'dopamin' in receptor:
                    receptors.add('dopaminergic')
                elif 'serotonin' in receptor:
                    receptors.add('serotonergic')
                elif 'histamin' in receptor:
                    receptors.add('histaminergic')
                elif 'opioid' in receptor or 'opio' in receptor:
                    receptors.add('opioid')
                elif 'gaba' in receptor.lower():
                    receptors.add('GABAergic')
                else:
                    receptors.add(receptor)

        return sorted(list(receptors))

    def extract_batch(self, interactions: list) -> list:
        """
        Extract mechanisms from multiple interactions.

        Args:
            interactions: List of dicts with 'effect' and 'recommendation' keys

        Returns:
            List of MechanismResult objects
        """
        results = []
        for interaction in interactions:
            effect = interaction.get('effect', interaction.get('efecto', ''))
            recommendation = interaction.get('recommendation', interaction.get('recomendacion', ''))
            results.append(self.extract(effect, recommendation))
        return results
