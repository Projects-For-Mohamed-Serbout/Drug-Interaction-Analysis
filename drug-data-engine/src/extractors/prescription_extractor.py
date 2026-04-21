"""
Extractor for the main Prescripcion.xml file.
Handles all drug/medication data including interactions.
"""
from pathlib import Path
from typing import List, Optional, Iterator
import xml.etree.ElementTree as ET
import logging

from .xml_extractor import XMLExtractor
from ..models.drug import (
    Drug,
    DrugPharmaceuticalForm,
    DrugComposition,
    DrugATC,
    DrugInteraction,
    Duplicity,
    GeriatricWarning,
    Biomarker,
    SupplyProblem
)

logger = logging.getLogger(__name__)


class PrescriptionExtractor(XMLExtractor):
    """Extracts drug data from Prescripcion.xml"""

    def __init__(self, file_path: Path):
        """
        Initialize the prescription extractor.

        Args:
            file_path: Path to Prescripcion.xml
        """
        super().__init__(file_path)
        self._drugs_count = 0
        self._interactions_count = 0

    def extract_drugs(self) -> Iterator[Drug]:
        """
        Extract all drugs from the prescription file.

        Yields:
            Drug objects
        """
        if not self.parse():
            return

        self._drugs_count = 0
        self._interactions_count = 0

        for prescription in self.find_all('prescription'):
            try:
                drug = self._extract_drug(prescription)
                self._drugs_count += 1

                if self._drugs_count % 1000 == 0:
                    logger.info(f"Extracted {self._drugs_count} drugs...")

                yield drug
            except Exception as e:
                cod_nacion = self.get_text(prescription, 'cod_nacion', 'unknown')
                logger.error(f"Error extracting drug {cod_nacion}: {e}")
                continue

        logger.info(f"Completed extraction: {self._drugs_count} drugs, {self._interactions_count} interactions")

    def _extract_drug(self, elem: ET.Element) -> Drug:
        """Extract a single drug from a prescription element."""
        drug = Drug(
            cod_nacion=self.get_text(elem, 'cod_nacion', ''),
            nro_definitivo=self.get_text(elem, 'nro_definitivo', ''),
            nombre_comercial=self.get_text(elem, 'des_nomco', ''),
            presentacion=self.get_text(elem, 'des_prese', ''),
            dosificacion=self.get_text(elem, 'des_dosific'),

            # SNOMED codes
            cod_dcsa=self.get_text(elem, 'cod_dcsa'),
            cod_dcp=self.get_text(elem, 'cod_dcp'),
            cod_dcpf=self.get_text(elem, 'cod_dcpf'),

            # Package info
            cod_envase=self.get_int(elem, 'cod_envase'),
            contenido=self.get_int(elem, 'contenido'),
            unid_contenido=self.get_int(elem, 'unid_contenido'),
            descripcion_contenido=self.get_text(elem, 'nro_conte'),

            # Classification flags
            es_psicotropo=self.get_bool(elem, 'sw_psicotropo'),
            es_estupefaciente=self.get_bool(elem, 'sw_estupefaciente'),
            afecta_conduccion=self.get_bool(elem, 'sw_afecta_conduccion'),
            triangulo_negro=self.get_bool(elem, 'sw_triangulo_negro'),
            requiere_receta=self.get_bool(elem, 'sw_receta'),
            es_generico=self.get_bool(elem, 'sw_generico'),
            es_sustituible=self.get_bool(elem, 'sw_sustituible'),
            envase_clinico=self.get_bool(elem, 'sw_envase_clinico'),
            uso_hospitalario=self.get_bool(elem, 'sw_uso_hospitalario'),
            diagnostico_hospitalario=self.get_bool(elem, 'sw_diagnostico_hospitalario'),
            tratamiento_larga_duracion=self.get_bool(elem, 'sw_tld'),
            control_medico_especial=self.get_bool(elem, 'sw_especial_control_medico'),
            es_huerfano=self.get_bool(elem, 'sw_huerfano'),
            base_plantas=self.get_bool(elem, 'sw_base_a_plantas'),
            es_biosimilar=self.get_bool(elem, 'biosimilar'),
            importacion_paralela=self.get_bool(elem, 'importacion_paralela'),
            es_radiofarmaco=self.get_bool(elem, 'radiofarmaco'),
            serializacion=self.get_bool(elem, 'serializacion'),
            tiene_excipientes_obligatorios=self.get_bool(elem, 'sw_tiene_excipientes_decl_obligatoria'),

            # Laboratory references
            laboratorio_titular=self.get_int(elem, 'laboratorio_titular'),
            laboratorio_comercializador=self.get_int(elem, 'laboratorio_comercializador'),

            # Dates
            fecha_autorizacion=self.get_text(elem, 'fecha_autorizacion'),
            fecha_comercializacion=self.get_text(elem, 'fec_comer'),
            fecha_situacion_registro=self.get_text(elem, 'fecha_situacion_registro'),

            # Status
            comercializado=self.get_bool(elem, 'sw_comercializado'),
            cod_situacion_registro=self.get_int(elem, 'cod_sitreg'),

            # URLs
            url_ficha_tecnica=self.get_text(elem, 'url_fictec'),
            url_prospecto=self.get_text(elem, 'url_prosp')
        )

        # Extract nested structures
        drug.formas_farmaceuticas = self._extract_pharmaceutical_forms(elem)
        drug.atc = self._extract_atc(elem)
        drug.biomarcadores = self._extract_biomarkers(elem)
        drug.problemas_suministro = self._extract_supply_problems(elem)

        return drug

    def _extract_pharmaceutical_forms(self, drug_elem: ET.Element) -> List[DrugPharmaceuticalForm]:
        """Extract pharmaceutical forms for a drug."""
        forms = []

        for form_elem in drug_elem.findall(f".//{self.namespace}formasfarmaceuticas"):
            form = DrugPharmaceuticalForm(
                codigo=self.get_int(form_elem, 'cod_forfar'),
                codigo_simplificado=self.get_int(form_elem, 'cod_forfar_simplificada'),
                numero_principios_activos=self.get_int(form_elem, 'nro_pactiv', 0)
            )

            # Extract composition
            form.composicion = self._extract_composition(form_elem)

            # Extract excipients
            for exc_elem in form_elem.findall(f".//{self.namespace}excipientes"):
                cod = self.get_int(exc_elem, 'cod_excipiente')
                if cod:
                    form.excipientes.append(cod)

            # Extract administration routes
            for via_elem in form_elem.findall(f".//{self.namespace}viasadministracion"):
                cod = self.get_int(via_elem, 'cod_via_admin')
                if cod:
                    form.vias_administracion.append(cod)

            forms.append(form)

        return forms

    def _extract_composition(self, form_elem: ET.Element) -> List[DrugComposition]:
        """Extract drug composition (active ingredients with dosage)."""
        compositions = []

        for comp_elem in form_elem.findall(f".//{self.namespace}composicion_pa"):
            composition = DrugComposition(
                codigo_principio_activo=self.get_int(comp_elem, 'cod_principio_activo'),
                orden=self.get_int(comp_elem, 'orden_colacion', 0),
                dosis=self.get_float(comp_elem, 'dosis_pa'),
                unidad_dosis=self.get_text(comp_elem, 'unidad_dosis_pa'),
                dosis_composicion=self.get_float(comp_elem, 'dosis_composicion'),
                unidad_composicion=self.get_text(comp_elem, 'unidad_composicion'),
                dosis_administracion=self.get_float(comp_elem, 'dosis_administracion'),
                unidad_administracion=self.get_text(comp_elem, 'unidad_administracion'),
                dosis_prescripcion=self.get_text(comp_elem, 'dosis_prescripcion'),
                unidad_prescripcion=self.get_text(comp_elem, 'unidad_prescripcion'),
                cantidad_volumen=self.get_float(comp_elem, 'cantidad_volumen_unidad_administracion'),
                unidad_volumen=self.get_text(comp_elem, 'unidad_volumen_unidad_administracion')
            )
            compositions.append(composition)

        return compositions

    def _extract_atc(self, drug_elem: ET.Element) -> Optional[DrugATC]:
        """Extract ATC classification with interactions."""
        atc_elem = drug_elem.find(f".//{self.namespace}atc")
        if atc_elem is None:
            return None

        atc = DrugATC(
            codigo=self.get_text(atc_elem, 'cod_atc', ''),
            teratogenia=self.get_text(atc_elem, 'teratogenia')
        )

        # Extract interactions - KEY DATA FOR THE PROJECT
        atc.interacciones = self._extract_interactions(atc_elem)
        self._interactions_count += len(atc.interacciones)

        # Extract duplicities
        atc.duplicidades = self._extract_duplicities(atc_elem)

        # Extract geriatric warnings
        atc.alertas_geriatria = self._extract_geriatric_warnings(atc_elem)

        return atc

    def _extract_interactions(self, atc_elem: ET.Element) -> List[DrugInteraction]:
        """Extract drug interactions from ATC element."""
        interactions = []

        for int_elem in atc_elem.findall(f".//{self.namespace}interacciones_atc"):
            interaction = DrugInteraction(
                atc_interaccion=self.get_text(int_elem, 'atc_interaccion', ''),
                descripcion=self.get_text(int_elem, 'descripcion_atc_interaccion', ''),
                efecto=self.get_text(int_elem, 'efecto_interaccion', ''),
                recomendacion=self.get_text(int_elem, 'recomendacion_interaccion', '')
            )
            interactions.append(interaction)

        return interactions

    def _extract_duplicities(self, atc_elem: ET.Element) -> List[Duplicity]:
        """Extract therapeutic duplicities."""
        duplicities = []

        for dup_elem in atc_elem.findall(f".//{self.namespace}duplicidades"):
            duplicity = Duplicity(
                atc_duplicidad=self.get_text(dup_elem, 'atc_duplicidad', ''),
                descripcion=self.get_text(dup_elem, 'descripcion_atc_duplicidad', ''),
                efecto=self.get_text(dup_elem, 'efecto_duplicidad', ''),
                recomendacion=self.get_text(dup_elem, 'recomendacion_duplicidad', '')
            )
            duplicities.append(duplicity)

        return duplicities

    def _extract_geriatric_warnings(self, atc_elem: ET.Element) -> List[GeriatricWarning]:
        """Extract geriatric warnings."""
        warnings = []

        for warn_elem in atc_elem.findall(f".//{self.namespace}desaconsejados_geriatria"):
            warning = GeriatricWarning(
                alerta=self.get_text(warn_elem, 'alerta_geriatria', ''),
                riesgo=self.get_text(warn_elem, 'riesgo_pacience_geriatria', ''),
                recomendacion=self.get_text(warn_elem, 'recomendacion_geriatria', '')
            )
            warnings.append(warning)

        return warnings

    def _extract_biomarkers(self, drug_elem: ET.Element) -> List[Biomarker]:
        """Extract biomarkers/pharmacogenomic markers."""
        biomarkers = []

        for bio_elem in drug_elem.findall(f".//{self.namespace}biomarcadores"):
            biomarker = Biomarker(
                clase=self.get_text(bio_elem, 'clase', ''),
                marcador=self.get_text(bio_elem, 'biomarcador', ''),
                genotipo_fenotipo=self.get_text(bio_elem, 'genotipo_fenotipo'),
                secciones_ft=self.get_text(bio_elem, 'secciones_ft'),
                descripcion=self.get_text(bio_elem, 'descripcion'),
                inclusion_sns=self.get_text(bio_elem, 'inclusion_cartera_sns', '').upper() == 'SÍ',
                notas=self.get_text(bio_elem, 'notas')
            )
            biomarkers.append(biomarker)

        return biomarkers

    def _extract_supply_problems(self, drug_elem: ET.Element) -> List[SupplyProblem]:
        """Extract supply problems."""
        problems = []

        for prob_elem in drug_elem.findall(f".//{self.namespace}problemassuministro"):
            problem = SupplyProblem(
                fecha_inicio=self.get_text(prob_elem, 'fecha_inicio'),
                fecha_fin=self.get_text(prob_elem, 'fecha_fin'),
                observaciones=self.get_text(prob_elem, 'observaciones')
            )
            problems.append(problem)

        return problems

    @property
    def drugs_count(self) -> int:
        """Get the number of drugs extracted."""
        return self._drugs_count

    @property
    def interactions_count(self) -> int:
        """Get the number of interactions extracted."""
        return self._interactions_count
