"""
Extractor for CIMA dictionary XML files.
Handles all reference data: active ingredients, laboratories, ATC codes, etc.
"""
from pathlib import Path
from typing import List, Dict, Any
import logging

from .xml_extractor import XMLExtractor
from ..models import (
    ActiveIngredient,
    Laboratory,
    ATCCode,
    PharmaceuticalForm,
    AdministrationRoute,
    Excipient,
    PackageType,
    ContentUnit,
    RegistrationStatus,
    DCSA,
    DCP,
    DCPF
)

logger = logging.getLogger(__name__)


class DictionaryExtractor:
    """Extracts reference data from CIMA dictionary XML files."""

    def __init__(self, xml_files: Dict[str, Path]):
        """
        Initialize the dictionary extractor.

        Args:
            xml_files: Dictionary mapping file names to paths
        """
        self.xml_files = xml_files

    def extract_active_ingredients(self) -> List[ActiveIngredient]:
        """Extract active ingredients from DICCIONARIO_PRINCIPIOS_ACTIVOS.xml"""
        extractor = XMLExtractor(self.xml_files['principios_activos'])
        if not extractor.parse():
            return []

        ingredients = []
        for elem in extractor.find_all('principiosactivos'):
            ingredient = ActiveIngredient(
                codigo=extractor.get_int(elem, 'nroprincipioactivo'),
                codigo_aemps=extractor.get_text(elem, 'codigoprincipioactivo', ''),
                nombre=extractor.get_text(elem, 'principioactivo', ''),
                lista_psicotropo=extractor.get_text(elem, 'listapsicotropo')
            )
            ingredients.append(ingredient)

        logger.info(f"Extracted {len(ingredients)} active ingredients")
        return ingredients

    def extract_laboratories(self) -> List[Laboratory]:
        """Extract laboratories from DICCIONARIO_LABORATORIOS.xml"""
        extractor = XMLExtractor(self.xml_files['laboratorios'])
        if not extractor.parse():
            return []

        laboratories = []
        for elem in extractor.find_all('laboratorios'):
            lab = Laboratory(
                codigo=extractor.get_int(elem, 'codigolaboratorio'),
                nombre=extractor.get_text(elem, 'laboratorio', ''),
                direccion=extractor.get_text(elem, 'direccion'),
                codigo_postal=extractor.get_text(elem, 'codigopostal'),
                localidad=extractor.get_text(elem, 'localidad'),
                cif=extractor.get_text(elem, 'cif')
            )
            laboratories.append(lab)

        logger.info(f"Extracted {len(laboratories)} laboratories")
        return laboratories

    def extract_atc_codes(self) -> List[ATCCode]:
        """Extract ATC codes from DICCIONARIO_ATC.xml"""
        extractor = XMLExtractor(self.xml_files['atc'])
        if not extractor.parse():
            return []

        atc_codes = []
        for elem in extractor.find_all('atc'):
            atc = ATCCode(
                nro=extractor.get_int(elem, 'nroatc'),
                codigo=extractor.get_text(elem, 'codigoatc', ''),
                descripcion=extractor.get_text(elem, 'descatc', '')
            )
            atc_codes.append(atc)

        logger.info(f"Extracted {len(atc_codes)} ATC codes")
        return atc_codes

    def extract_pharmaceutical_forms(self) -> List[PharmaceuticalForm]:
        """Extract pharmaceutical forms from DICCIONARIO_FORMA_FARMACEUTICA.xml"""
        extractor = XMLExtractor(self.xml_files['forma_farmaceutica'])
        if not extractor.parse():
            return []

        forms = []
        for elem in extractor.find_all('formasfarmaceuticas'):
            form = PharmaceuticalForm(
                codigo=extractor.get_int(elem, 'codigoformafarmaceutica'),
                nombre=extractor.get_text(elem, 'formafarmaceutica', ''),
                codigo_simplificado=extractor.get_int(elem, 'codigoformafarmaceuticasimplificada')
            )
            forms.append(form)

        logger.info(f"Extracted {len(forms)} pharmaceutical forms")
        return forms

    def extract_simplified_pharmaceutical_forms(self) -> List[PharmaceuticalForm]:
        """Extract simplified pharmaceutical forms."""
        extractor = XMLExtractor(self.xml_files['forma_farmaceutica_simplificada'])
        if not extractor.parse():
            return []

        forms = []
        for elem in extractor.find_all('formasfarmaceuticassimplificadas'):
            form = PharmaceuticalForm(
                codigo=extractor.get_int(elem, 'codigoformafarmaceuticasimplificada'),
                nombre=extractor.get_text(elem, 'formafarmaceuticasimplificada', '')
            )
            forms.append(form)

        logger.info(f"Extracted {len(forms)} simplified pharmaceutical forms")
        return forms

    def extract_administration_routes(self) -> List[AdministrationRoute]:
        """Extract administration routes from DICCIONARIO_VIAS_ADMINISTRACION.xml"""
        extractor = XMLExtractor(self.xml_files['vias_administracion'])
        if not extractor.parse():
            return []

        routes = []
        for elem in extractor.find_all('viasadministracion'):
            route = AdministrationRoute(
                codigo=extractor.get_int(elem, 'codigoviaadministracion'),
                nombre=extractor.get_text(elem, 'viaadministracion', '')
            )
            routes.append(route)

        logger.info(f"Extracted {len(routes)} administration routes")
        return routes

    def extract_excipients(self) -> List[Excipient]:
        """Extract excipients from DICCIONARIO_EXCIPIENTES_DECL_OBLIGATORIA.xml"""
        extractor = XMLExtractor(self.xml_files['excipientes'])
        if not extractor.parse():
            return []

        excipients = []
        for elem in extractor.find_all('excipientes'):
            excipient = Excipient(
                codigo=extractor.get_int(elem, 'codigoedo'),
                nombre=extractor.get_text(elem, 'edo', '')
            )
            excipients.append(excipient)

        logger.info(f"Extracted {len(excipients)} excipients")
        return excipients

    def extract_package_types(self) -> List[PackageType]:
        """Extract package types from DICCIONARIO_ENVASES.xml"""
        extractor = XMLExtractor(self.xml_files['envases'])
        if not extractor.parse():
            return []

        packages = []
        for elem in extractor.find_all('envases'):
            package = PackageType(
                codigo=extractor.get_int(elem, 'codigoenvase'),
                nombre=extractor.get_text(elem, 'envase', '')
            )
            packages.append(package)

        logger.info(f"Extracted {len(packages)} package types")
        return packages

    def extract_content_units(self) -> List[ContentUnit]:
        """Extract content units from DICCIONARIO_UNIDAD_CONTENIDO.xml"""
        extractor = XMLExtractor(self.xml_files['unidad_contenido'])
        if not extractor.parse():
            return []

        units = []
        for elem in extractor.find_all('unidadescontenido'):
            unit = ContentUnit(
                codigo=extractor.get_int(elem, 'codigounidadcontenido'),
                nombre=extractor.get_text(elem, 'unidadcontenido', '')
            )
            units.append(unit)

        logger.info(f"Extracted {len(units)} content units")
        return units

    def extract_registration_statuses(self) -> List[RegistrationStatus]:
        """Extract registration statuses from DICCIONARIO_SITUACION_REGISTRO.xml"""
        extractor = XMLExtractor(self.xml_files['situacion_registro'])
        if not extractor.parse():
            return []

        statuses = []
        for elem in extractor.find_all('situacionesregistro'):
            status = RegistrationStatus(
                codigo=extractor.get_int(elem, 'codigosituacionregistro'),
                descripcion=extractor.get_text(elem, 'situacionregistro', '')
            )
            statuses.append(status)

        logger.info(f"Extracted {len(statuses)} registration statuses")
        return statuses

    def extract_dcsa(self) -> List[DCSA]:
        """Extract SNOMED CT substance codes from DICCIONARIO_DCSA.xml"""
        extractor = XMLExtractor(self.xml_files['dcsa'])
        if not extractor.parse():
            return []

        items = []
        for elem in extractor.find_all('dcsa'):
            item = DCSA(
                codigo=extractor.get_text(elem, 'codigodcsa', ''),
                nombre=extractor.get_text(elem, 'nombredcsa', '')
            )
            items.append(item)

        logger.info(f"Extracted {len(items)} DCSA codes")
        return items

    def extract_dcp(self) -> List[DCP]:
        """Extract SNOMED CT clinical drug codes from DICCIONARIO_DCP.xml"""
        extractor = XMLExtractor(self.xml_files['dcp'])
        if not extractor.parse():
            return []

        items = []
        for elem in extractor.find_all('dcp'):
            item = DCP(
                codigo=extractor.get_text(elem, 'codigodcp', ''),
                nombre=extractor.get_text(elem, 'nombredcp', ''),
                codigo_dcsa=extractor.get_text(elem, 'codigodcsa', '')
            )
            items.append(item)

        logger.info(f"Extracted {len(items)} DCP codes")
        return items

    def extract_dcpf(self) -> List[DCPF]:
        """Extract SNOMED CT clinical drug + form codes from DICCIONARIO_DCPF.xml"""
        extractor = XMLExtractor(self.xml_files['dcpf'])
        if not extractor.parse():
            return []

        items = []
        for elem in extractor.find_all('dcpf'):
            item = DCPF(
                codigo=extractor.get_text(elem, 'codigodcpf', ''),
                nombre=extractor.get_text(elem, 'nombredcpf', ''),
                codigo_dcp=extractor.get_text(elem, 'codigodcp', '')
            )
            items.append(item)

        logger.info(f"Extracted {len(items)} DCPF codes")
        return items

    def extract_all(self) -> Dict[str, List[Any]]:
        """
        Extract all dictionary data.

        Returns:
            Dictionary with all extracted reference data
        """
        logger.info("Starting extraction of all dictionary data...")

        data = {
            'active_ingredients': self.extract_active_ingredients(),
            'laboratories': self.extract_laboratories(),
            'atc_codes': self.extract_atc_codes(),
            'pharmaceutical_forms': self.extract_pharmaceutical_forms(),
            'simplified_pharmaceutical_forms': self.extract_simplified_pharmaceutical_forms(),
            'administration_routes': self.extract_administration_routes(),
            'excipients': self.extract_excipients(),
            'package_types': self.extract_package_types(),
            'content_units': self.extract_content_units(),
            'registration_statuses': self.extract_registration_statuses(),
            'dcsa': self.extract_dcsa(),
            'dcp': self.extract_dcp(),
            'dcpf': self.extract_dcpf()
        }

        logger.info("Completed extraction of all dictionary data")
        return data
