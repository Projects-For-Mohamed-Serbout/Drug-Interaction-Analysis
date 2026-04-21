"""
Interaction Type Classifier using spaCy and NLTK - IMPROVED VERSION.

This implementation uses:
- spaCy for tokenization, lemmatization, and named entity recognition
- NLTK for additional text processing
- BOTH token matching AND lemma matching for comprehensive coverage
- Regex phrase patterns for better compound term detection
- Semantic similarity with word vectors (when available)
"""

import spacy
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import nltk
from collections import defaultdict

logger = logging.getLogger(__name__)


class InteractionType(Enum):
    """Types of drug interaction effects."""
    CARDIAC = "cardiac"
    HEMORRHAGIC = "hemorrhagic"
    CNS = "cns"
    METABOLIC = "metabolic"
    RENAL = "renal"
    HEPATIC = "hepatic"
    RESPIRATORY = "respiratory"
    GASTROINTESTINAL = "gastrointestinal"
    MUSCULAR = "muscular"
    HEMATOLOGIC = "hematologic"
    EFFICACY_REDUCTION = "efficacy_reduction"
    EFFICACY_INCREASE = "efficacy_increase"
    TOXICITY = "toxicity"
    OTHER = "other"


@dataclass
class InteractionTypeResult:
    """Result of interaction type classification."""
    primary_type: InteractionType
    secondary_types: List[InteractionType]
    confidence: float
    matched_terms: Dict[str, List[str]]
    effect_category: str
    linguistic_analysis: Dict


class InteractionTypeClassifierSpacy:
    """
    Classifies drug interactions by clinical effect type using spaCy.

    IMPROVED VERSION - Key changes:
    1. Matches BOTH original tokens AND lemmas
    2. Uses regex patterns for key medical phrases
    3. Higher weights for compound clinical terms
    4. Better handling of Spanish medical terminology
    """

    def __init__(self, model_name: str = "es_core_news_md"):
        """Initialize the spaCy-based interaction type classifier."""
        self.model_name = model_name
        self._load_model()
        self._init_phrase_patterns()
        self._init_type_lexicons()
        self._init_effect_categories()

    def _load_model(self):
        """Load spaCy Spanish model."""
        try:
            self.nlp = spacy.load(self.model_name)
            logger.info(f"Loaded spaCy model: {self.model_name}")
        except OSError:
            logger.warning(f"Model {self.model_name} not found, downloading...")
            spacy.cli.download(self.model_name)
            self.nlp = spacy.load(self.model_name)

        # Check if model has word vectors
        self.has_vectors = self.nlp.vocab.vectors.shape[0] > 0
        if self.has_vectors:
            logger.info("Model has word vectors - semantic similarity enabled")

    def _init_phrase_patterns(self):
        """
        Initialize regex patterns for detecting key medical phrases.

        These patterns catch multi-word expressions that indicate specific interaction types.
        """
        # CARDIAC patterns
        self.cardiac_patterns = [
            (re.compile(r'\barritmias?\s+ventriculares?\b', re.IGNORECASE), 2.0),
            (re.compile(r'\btorsade[s]?\s+de\s+pointes\b', re.IGNORECASE), 2.5),
            (re.compile(r'\bprolongaci[oó]n\s+(?:del?\s+)?(?:intervalo\s+)?QT\b', re.IGNORECASE), 2.0),
            (re.compile(r'\bintervalo\s+QT\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bparo\s+card[ií]aco\b', re.IGNORECASE), 2.0),
            (re.compile(r'\bfibrilaci[oó]n\s+(?:ventricular|auricular)\b', re.IGNORECASE), 2.0),
            (re.compile(r'\binsuficiencia\s+card[ií]aca\b', re.IGNORECASE), 1.5),
            (re.compile(r'\briesgo\s+cardiovascular\b', re.IGNORECASE), 1.2),
            (re.compile(r'\bbloqueo\s+(?:AV|auriculoventricular|card[ií]aco)\b', re.IGNORECASE), 1.5),
            (re.compile(r'\btaquicardia\s+ventricular\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bbradicardia\s+(?:severa|grave|sinusal)?\b', re.IGNORECASE), 1.2),
        ]

        # HEMORRHAGIC patterns
        self.hemorrhagic_patterns = [
            (re.compile(r'\briesgo\s+(?:de\s+)?hemorragia\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bhemorragia\s+(?:digestiva|gastrointestinal|cerebral|grave)\b', re.IGNORECASE), 2.0),
            (re.compile(r'\bsangrado\s+(?:gastrointestinal|digestivo|grave)\b', re.IGNORECASE), 1.8),
            (re.compile(r'\befecto\s+anticoagulante\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bmonitorizar\s+INR\b', re.IGNORECASE), 1.5),
            (re.compile(r'\btiempo\s+de\s+protrombina\b', re.IGNORECASE), 1.3),
            (re.compile(r'\bsignos\s+de\s+sangrado\b', re.IGNORECASE), 1.5),
        ]

        # CNS patterns
        self.cns_patterns = [
            (re.compile(r'\bs[ií]ndrome\s+serotonin[eé]rgico\b', re.IGNORECASE), 2.5),
            (re.compile(r'\bdepresi[oó]n\s+(?:del?\s+)?SNC\b', re.IGNORECASE), 2.0),
            (re.compile(r'\befecto\s+sedante\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bsobre\s+(?:el\s+)?SNC\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bsistema\s+nervioso\s+central\b', re.IGNORECASE), 1.2),
            (re.compile(r'\bconvulsiones?\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bencefalopatia\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bs[ií]ntomas?\s+extrapiramidales?\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bsomnolencia\s+(?:excesiva|grave)?\b', re.IGNORECASE), 1.2),
        ]

        # METABOLIC patterns
        self.metabolic_patterns = [
            (re.compile(r'\bhiperpotasemia\s+(?:severa|grave)?\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bhipopotasemia\s+(?:severa|grave)?\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bhipoglucemia\s+(?:severa|grave)?\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bhiperglucemia\b', re.IGNORECASE), 1.3),
            (re.compile(r'\bniveles?\s+de\s+potasio\b', re.IGNORECASE), 1.5),
            (re.compile(r'\belectrolitos?\b', re.IGNORECASE), 1.0),
            (re.compile(r'\balteraci[oó]n\s+metab[oó]lica\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bacidosis\s+(?:metab[oó]lica|l[aá]ctica)\b', re.IGNORECASE), 1.8),
        ]

        # RENAL patterns
        self.renal_patterns = [
            (re.compile(r'\bnefrotoxicidad\b', re.IGNORECASE), 2.0),
            (re.compile(r'\binsuficiencia\s+renal\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bfunci[oó]n\s+renal\b', re.IGNORECASE), 1.5),
            (re.compile(r'\baclaramiento\s+(?:renal|de\s+creatinina)\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bda[ñn]o\s+renal\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bnecrosis\s+tubular\b', re.IGNORECASE), 2.0),
        ]

        # HEPATIC patterns
        self.hepatic_patterns = [
            (re.compile(r'\bhepatotoxicidad\b', re.IGNORECASE), 2.0),
            (re.compile(r'\binsuficiencia\s+hep[aá]tica\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bfunci[oó]n\s+hep[aá]tica\b', re.IGNORECASE), 1.5),
            (re.compile(r'\btransaminasas?\b', re.IGNORECASE), 1.3),
            (re.compile(r'\bictericia\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bcolestasis\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bmetabolismo\s+hep[aá]tico\b', re.IGNORECASE), 1.5),
        ]

        # RESPIRATORY patterns
        self.respiratory_patterns = [
            (re.compile(r'\bdepresi[oó]n\s+respiratoria\b', re.IGNORECASE), 2.0),
            (re.compile(r'\binsuficiencia\s+respiratoria\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bbroncoespasmo\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bdisnea\b', re.IGNORECASE), 1.2),
            (re.compile(r'\bapnea\b', re.IGNORECASE), 1.5),
        ]

        # GASTROINTESTINAL patterns
        self.gastrointestinal_patterns = [
            (re.compile(r'\b[uú]lcera\s+(?:g[aá]strica|digestiva|gastrointestinal)\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bperforaci[oó]n\s+(?:g[aá]strica|intestinal)\b', re.IGNORECASE), 2.0),
            (re.compile(r'\bpancreatitis\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bgastritis\b', re.IGNORECASE), 1.3),
            (re.compile(r'\btoxicidad\s+gastrointestinal\b', re.IGNORECASE), 1.5),
        ]

        # MUSCULAR patterns
        self.muscular_patterns = [
            (re.compile(r'\brabdomi[oó]lisis\b', re.IGNORECASE), 2.5),
            (re.compile(r'\bmiopat[ií]a\b', re.IGNORECASE), 2.0),
            (re.compile(r'\bdebilidad\s+muscular\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bmialgia\b', re.IGNORECASE), 1.2),
            (re.compile(r'\bCPK\s+elevad[ao]\b', re.IGNORECASE), 1.8),
        ]

        # HEMATOLOGIC patterns
        self.hematologic_patterns = [
            (re.compile(r'\bagranulocitosis\b', re.IGNORECASE), 2.0),
            (re.compile(r'\bneutropenia\b', re.IGNORECASE), 1.8),
            (re.compile(r'\btrombocitopenia\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bpancitopenia\b', re.IGNORECASE), 2.0),
            (re.compile(r'\baplasia\s+medular\b', re.IGNORECASE), 2.0),
            (re.compile(r'\banemia\s+(?:apl[aá]sica|hemol[ií]tica)?\b', re.IGNORECASE), 1.3),
        ]

        # EFFICACY REDUCTION patterns
        self.efficacy_reduction_patterns = [
            (re.compile(r'\bdisminuci[oó]n\s+del?\s+efecto\b', re.IGNORECASE), 2.0),
            (re.compile(r'\breducci[oó]n\s+del?\s+efecto\b', re.IGNORECASE), 2.0),
            (re.compile(r'\bmenor\s+eficacia\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bp[eé]rdida\s+(?:de\s+)?eficacia\b', re.IGNORECASE), 1.8),
            (re.compile(r'\binducci[oó]n\s+(?:del?\s+)?metabolismo\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bfallo\s+terap[eé]utico\b', re.IGNORECASE), 2.0),
            (re.compile(r'\bcompromete\s+(?:la\s+)?eficacia\b', re.IGNORECASE), 1.8),
        ]

        # EFFICACY INCREASE patterns
        self.efficacy_increase_patterns = [
            (re.compile(r'\baumento\s+del?\s+efecto\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bpotenciaci[oó]n\s+del?\s+efecto\b', re.IGNORECASE), 2.0),
            (re.compile(r'\befecto\s+(?:aditivo|sin[eé]rgico)\b', re.IGNORECASE), 1.5),
            (re.compile(r'\binhibici[oó]n\s+(?:del?\s+)?metabolismo\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bniveles?\s+plasm[aá]ticos?\s+(?:elevados?|aumentados?)\b', re.IGNORECASE), 1.5),
        ]

        # TOXICITY patterns
        self.toxicity_patterns = [
            (re.compile(r'\baumento\s+(?:de\s+)?(?:la\s+)?toxicidad\b', re.IGNORECASE), 2.0),
            (re.compile(r'\btoxicidad\s+(?:grave|severa|aumentada)\b', re.IGNORECASE), 2.0),
            (re.compile(r'\bintoxicaci[oó]n\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bsobredosis\b', re.IGNORECASE), 1.8),
            (re.compile(r'\bacumulaci[oó]n\s+(?:del?\s+)?f[aá]rmaco\b', re.IGNORECASE), 1.5),
            (re.compile(r'\bconcentraci[oó]n\s+(?:plasm[aá]tica\s+)?elevada\b', re.IGNORECASE), 1.3),
        ]

        # Map patterns to types
        self.type_patterns = {
            InteractionType.CARDIAC: self.cardiac_patterns,
            InteractionType.HEMORRHAGIC: self.hemorrhagic_patterns,
            InteractionType.CNS: self.cns_patterns,
            InteractionType.METABOLIC: self.metabolic_patterns,
            InteractionType.RENAL: self.renal_patterns,
            InteractionType.HEPATIC: self.hepatic_patterns,
            InteractionType.RESPIRATORY: self.respiratory_patterns,
            InteractionType.GASTROINTESTINAL: self.gastrointestinal_patterns,
            InteractionType.MUSCULAR: self.muscular_patterns,
            InteractionType.HEMATOLOGIC: self.hematologic_patterns,
            InteractionType.EFFICACY_REDUCTION: self.efficacy_reduction_patterns,
            InteractionType.EFFICACY_INCREASE: self.efficacy_increase_patterns,
            InteractionType.TOXICITY: self.toxicity_patterns,
        }

    def _init_type_lexicons(self):
        """
        Initialize lexicons for each interaction type.

        IMPROVED: Using BOTH tokens (original forms) AND lemmas for better matching.
        """

        # CARDIAC - Tokens and Lemmas
        self.cardiac_tokens = {
            # Original tokens (as they appear in text)
            'arritmia', 'arritmias', 'taquicardia', 'bradicardia',
            'fibrilación', 'fibrilacion', 'cardíaco', 'cardiaco', 'cardíaca', 'cardiaca',
            'corazón', 'corazon', 'infarto', 'isquemia', 'isquémico', 'isquemico',
            'paro', 'bloqueo', 'extrasístole', 'extrasistole', 'qt',
            'torsade', 'pointes', 'ventricular', 'ventriculares',
            'auricular', 'auriculares', 'coronario', 'coronaria',
            'vasoconstricción', 'vasoconstriccion', 'vasodilatación', 'vasodilatacion',
            'hipertensión', 'hipertension', 'hipotensión', 'hipotension',
            'cardiovascular',
        }
        self.cardiac_lemmas = {
            'arritmia', 'taquicardia', 'bradicardia', 'fibrilación',
            'cardíaco', 'corazón', 'infarto', 'isquemia',
            'ventricular', 'auricular', 'coronario',
        }

        # HEMORRHAGIC - Tokens and Lemmas
        self.hemorrhagic_tokens = {
            'hemorragia', 'hemorragias', 'hemorrágico', 'hemorragico',
            'sangrado', 'sangrados', 'sangrar',
            'anticoagulante', 'anticoagulantes', 'inr',
            'protrombina', 'plaqueta', 'plaquetas', 'plaquetario',
            'trombocitopenia', 'equimosis', 'hematoma', 'hematomas',
            'epistaxis', 'melena', 'hematemesis', 'petequia', 'petequias',
            'coagulación', 'coagulacion',
        }
        self.hemorrhagic_lemmas = {
            'hemorragia', 'hemorrágico', 'sangrado', 'sangrar',
            'anticoagulante', 'coagulación', 'plaqueta',
        }

        # CNS - Tokens and Lemmas
        self.cns_tokens = {
            'sedación', 'sedacion', 'sedante', 'sedantes',
            'somnolencia', 'snc', 'convulsión', 'convulsion',
            'convulsiones', 'epilepsia', 'epiléptico', 'epileptico',
            'neurológico', 'neurologico', 'neurológica', 'neurologica',
            'extrapiramidal', 'extrapiramidales',
            'discinesia', 'distonía', 'distonia', 'acatisia',
            'parkinson', 'parkinsoniano', 'temblor', 'temblores', 'ataxia',
            'confusión', 'confusion', 'delirio', 'alucinación', 'alucinacion',
            'serotoninérgico', 'serotoninergico', 'serotonina',
            'anticolinérgico', 'anticolinergico',
            'coma', 'encefalopatía', 'encefalopatia',
        }
        self.cns_lemmas = {
            'sedación', 'sedante', 'somnolencia', 'convulsión',
            'neurológico', 'extrapiramidal', 'temblor', 'confusión',
            'serotonina', 'anticolinérgico',
        }

        # METABOLIC - Tokens and Lemmas
        self.metabolic_tokens = {
            'hipopotasemia', 'hiperpotasemia', 'hiponatremia', 'hipernatremia',
            'hipocalcemia', 'hipercalcemia', 'hipoglucemia', 'hiperglucemia',
            'electrolito', 'electrolitos', 'electrolítico', 'electrolitico',
            'acidosis', 'alcalosis', 'hiperuricemia', 'gota',
            'deshidratación', 'deshidratacion', 'metabólico', 'metabolico',
            'potasio', 'sodio', 'calcio', 'glucosa',
        }
        self.metabolic_lemmas = {
            'hipopotasemia', 'hiperpotasemia', 'hipoglucemia',
            'electrolito', 'acidosis', 'metabólico',
        }

        # RENAL - Tokens and Lemmas
        self.renal_tokens = {
            'nefrotoxicidad', 'nefrotóxico', 'nefrotoxic',
            'renal', 'renales', 'riñón', 'rinon',
            'aclaramiento', 'creatinina', 'diuresis',
            'oliguria', 'anuria', 'nefrosis', 'nefritis',
            'glomerular', 'tubular', 'urinario', 'urinaria',
        }
        self.renal_lemmas = {
            'nefrotoxicidad', 'renal', 'riñón', 'creatinina',
            'diuresis', 'glomerular',
        }

        # HEPATIC - Tokens and Lemmas
        self.hepatic_tokens = {
            'hepatotoxicidad', 'hepatotóxico', 'hepatotoxico',
            'hepático', 'hepatico', 'hepática', 'hepatica',
            'transaminasa', 'transaminasas', 'alt', 'ast', 'ggt',
            'bilirrubina', 'ictericia', 'colestasis',
            'hepatitis', 'hígado', 'higado', 'cirrosis',
        }
        self.hepatic_lemmas = {
            'hepatotoxicidad', 'hepático', 'transaminasa',
            'bilirrubina', 'ictericia', 'hígado',
        }

        # RESPIRATORY - Tokens and Lemmas
        self.respiratory_tokens = {
            'respiratorio', 'respiratoria',
            'broncoespasmo', 'asma', 'asmático', 'asmatico',
            'disnea', 'apnea', 'hipoxia', 'hipoxemia',
            'neumonía', 'neumonia', 'fibrosis', 'pulmonar', 'pulmón', 'pulmon',
        }
        self.respiratory_lemmas = {
            'respiratorio', 'broncoespasmo', 'asma', 'disnea',
            'pulmonar', 'pulmón',
        }

        # GASTROINTESTINAL - Tokens and Lemmas
        self.gastrointestinal_tokens = {
            'úlcera', 'ulcera', 'gastritis', 'gastrointestinal',
            'digestivo', 'digestiva', 'náusea', 'nausea', 'náuseas', 'nauseas',
            'vómito', 'vomito', 'vómitos', 'vomitos',
            'diarrea', 'estreñimiento', 'estrenimiento',
            'pancreatitis', 'dispepsia', 'perforación', 'perforacion',
            'gástrico', 'gastrico', 'intestinal', 'esofágico', 'esofagico',
        }
        self.gastrointestinal_lemmas = {
            'úlcera', 'gastritis', 'gastrointestinal', 'digestivo',
            'náusea', 'vómito', 'diarrea', 'gástrico',
        }

        # MUSCULAR - Tokens and Lemmas
        self.muscular_tokens = {
            'miopatía', 'miopatia', 'rabdomiólisis', 'rabdomiolisis',
            'muscular', 'musculares', 'mialgia', 'mialgias',
            'calambre', 'calambres', 'cpk', 'creatinfosfoquinasa',
            'músculo', 'musculo', 'debilidad',
        }
        self.muscular_lemmas = {
            'miopatía', 'rabdomiólisis', 'muscular', 'mialgia',
            'calambre', 'músculo',
        }

        # HEMATOLOGIC - Tokens and Lemmas
        self.hematologic_tokens = {
            'agranulocitosis', 'neutropenia', 'leucopenia',
            'pancitopenia', 'aplasia', 'anemia',
            'médula', 'medula', 'hematopoyético', 'hematopoyetico',
            'hematológico', 'hematologico',
            'eritrocito', 'eritrocitos', 'leucocito', 'leucocitos',
        }
        self.hematologic_lemmas = {
            'agranulocitosis', 'neutropenia', 'pancitopenia',
            'anemia', 'médula', 'hematológico',
        }

        # EFFICACY REDUCTION - Tokens and Lemmas
        self.efficacy_reduction_tokens = {
            'disminución', 'disminucion', 'reducción', 'reduccion',
            'menor', 'pérdida', 'perdida', 'fallo',
            'antagonismo', 'antagonista', 'inhibición', 'inhibicion',
            'ineficacia', 'ineficaz', 'inductor', 'inductores',
            'inducción', 'induccion',
        }
        self.efficacy_reduction_lemmas = {
            'disminuir', 'reducir', 'perder', 'antagonizar', 'inhibir',
        }

        # EFFICACY INCREASE - Tokens and Lemmas
        self.efficacy_increase_tokens = {
            'aumento', 'potenciación', 'potenciacion',
            'sinergismo', 'sinergia', 'sinérgico', 'sinergico',
            'aditivo', 'incremento', 'mayor',
            'inhibidor', 'inhibidores',
        }
        self.efficacy_increase_lemmas = {
            'aumentar', 'potenciar', 'incrementar',
        }

        # TOXICITY - Tokens and Lemmas
        self.toxicity_tokens = {
            'toxicidad', 'tóxico', 'toxico', 'tóxica', 'toxica',
            'intoxicación', 'intoxicacion', 'sobredosis',
            'acumulación', 'acumulacion', 'concentración', 'concentracion',
        }
        self.toxicity_lemmas = {
            'toxicidad', 'tóxico', 'intoxicación', 'acumular',
        }

        # Map types to token and lemma sets
        self.type_tokens = {
            InteractionType.CARDIAC: self.cardiac_tokens,
            InteractionType.HEMORRHAGIC: self.hemorrhagic_tokens,
            InteractionType.CNS: self.cns_tokens,
            InteractionType.METABOLIC: self.metabolic_tokens,
            InteractionType.RENAL: self.renal_tokens,
            InteractionType.HEPATIC: self.hepatic_tokens,
            InteractionType.RESPIRATORY: self.respiratory_tokens,
            InteractionType.GASTROINTESTINAL: self.gastrointestinal_tokens,
            InteractionType.MUSCULAR: self.muscular_tokens,
            InteractionType.HEMATOLOGIC: self.hematologic_tokens,
            InteractionType.EFFICACY_REDUCTION: self.efficacy_reduction_tokens,
            InteractionType.EFFICACY_INCREASE: self.efficacy_increase_tokens,
            InteractionType.TOXICITY: self.toxicity_tokens,
        }

        self.type_lemmas = {
            InteractionType.CARDIAC: self.cardiac_lemmas,
            InteractionType.HEMORRHAGIC: self.hemorrhagic_lemmas,
            InteractionType.CNS: self.cns_lemmas,
            InteractionType.METABOLIC: self.metabolic_lemmas,
            InteractionType.RENAL: self.renal_lemmas,
            InteractionType.HEPATIC: self.hepatic_lemmas,
            InteractionType.RESPIRATORY: self.respiratory_lemmas,
            InteractionType.GASTROINTESTINAL: self.gastrointestinal_lemmas,
            InteractionType.MUSCULAR: self.muscular_lemmas,
            InteractionType.HEMATOLOGIC: self.hematologic_lemmas,
            InteractionType.EFFICACY_REDUCTION: self.efficacy_reduction_lemmas,
            InteractionType.EFFICACY_INCREASE: self.efficacy_increase_lemmas,
            InteractionType.TOXICITY: self.toxicity_lemmas,
        }

    def _init_effect_categories(self):
        """Map interaction types to clinical effect categories."""
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

    def _score_patterns(self, text: str, patterns: List[Tuple]) -> Tuple[float, List[str]]:
        """Score text against regex patterns."""
        score = 0.0
        matched = []

        for pattern, weight in patterns:
            matches = pattern.findall(text)
            if matches:
                score += weight * len(matches)
                matched.extend(matches if isinstance(matches[0], str) else [m[0] for m in matches])

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

    def classify(self, effect: str, recommendation: str = "") -> InteractionTypeResult:
        """
        Classify the type of drug interaction using spaCy.

        IMPROVED: Uses both pattern matching AND token/lemma matching.
        """
        text = f"{effect} {recommendation}".strip()

        if not text:
            return InteractionTypeResult(
                primary_type=InteractionType.OTHER,
                secondary_types=[],
                confidence=0.0,
                matched_terms={},
                effect_category="Unclassified",
                linguistic_analysis={}
            )

        # Process with spaCy
        doc = self.nlp(text)

        # Extract tokens and lemmas
        tokens = [token.text.lower() for token in doc if not token.is_punct and not token.is_space]
        lemmas = [token.lemma_.lower() for token in doc if not token.is_punct and not token.is_space]

        # Score each type using BOTH patterns AND tokens/lemmas
        scores: Dict[InteractionType, float] = {}
        all_matched: Dict[InteractionType, List[str]] = {}

        for itype in InteractionType:
            if itype == InteractionType.OTHER:
                continue

            total_score = 0.0
            matched_terms = []

            # 1. Score with regex patterns (higher priority for phrases)
            if itype in self.type_patterns:
                pattern_score, pattern_matched = self._score_patterns(text, self.type_patterns[itype])
                total_score += pattern_score * 1.5  # Boost pattern matches
                matched_terms.extend(pattern_matched)

            # 2. Score with token/lemma matching
            if itype in self.type_tokens and itype in self.type_lemmas:
                token_score, token_matched = self._score_tokens_and_lemmas(
                    tokens, lemmas,
                    self.type_tokens[itype],
                    self.type_lemmas[itype],
                    weight=1.0
                )
                total_score += token_score
                matched_terms.extend(token_matched)

            if total_score > 0:
                scores[itype] = total_score
                all_matched[itype] = matched_terms

        # Determine result
        if not scores:
            return InteractionTypeResult(
                primary_type=InteractionType.OTHER,
                secondary_types=[],
                confidence=0.3,
                matched_terms={},
                effect_category="Unclassified",
                linguistic_analysis={
                    'tokens_analyzed': len(tokens),
                }
            )

        # Sort by score
        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        primary_type = sorted_types[0][0]
        primary_score = sorted_types[0][1]

        # Get secondary types (score >= 1 and at least 30% of primary score)
        secondary_types = [
            t for t, s in sorted_types[1:4]
            if s >= 1.0 and s >= primary_score * 0.3
        ]

        # Calculate confidence
        total_score = sum(scores.values())
        confidence = min(0.95, 0.4 + (primary_score / max(total_score, 1)) * 0.5)

        # Boost confidence for multiple matches
        if len(all_matched.get(primary_type, [])) > 2:
            confidence = min(0.98, confidence + 0.1)

        # Build matched terms dict
        matched_terms = {t.value: list(set(m)) for t, m in all_matched.items()}

        return InteractionTypeResult(
            primary_type=primary_type,
            secondary_types=secondary_types,
            confidence=confidence,
            matched_terms=matched_terms,
            effect_category=self.effect_categories[primary_type],
            linguistic_analysis={
                'tokens_analyzed': len(tokens),
                'patterns_matched': sum(1 for patterns in self.type_patterns.values()
                                        for p, _ in patterns if p.search(text)),
                'types_detected': len(scores),
            }
        )

    def classify_batch(self, interactions: List[Dict]) -> List[InteractionTypeResult]:
        """
        Classify multiple interactions using spaCy pipe.

        Args:
            interactions: List of dicts with 'effect'/'efecto' and 'recommendation'/'recomendacion'

        Returns:
            List of InteractionTypeResult objects
        """
        results = []

        for interaction in interactions:
            effect = interaction.get('effect', interaction.get('efecto', ''))
            recommendation = interaction.get('recommendation', interaction.get('recomendacion', ''))
            results.append(self.classify(effect, recommendation))

        return results
