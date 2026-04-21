"""
Data Transformer for enriching and preparing data for loading.
Handles denormalization and data enrichment.
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from ..models.drug import Drug

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transforms and enriches extracted data for database loading."""

    def __init__(self, reference_data: Dict[str, List[Any]]):
        """
        Initialize the transformer with reference data.

        Args:
            reference_data: Dictionary containing all reference collections
        """
        self.reference_data = reference_data
        self._build_lookup_tables()

    def _build_lookup_tables(self):
        """Build lookup tables for quick reference resolution."""
        logger.info("Building lookup tables...")

        # Active ingredients by code
        self.active_ingredients = {
            item.codigo: item for item in self.reference_data.get('active_ingredients', [])
        }

        # Laboratories by code
        self.laboratories = {
            item.codigo: item for item in self.reference_data.get('laboratories', [])
        }

        # ATC codes by code string
        self.atc_codes = {
            item.codigo: item for item in self.reference_data.get('atc_codes', [])
        }

        # Pharmaceutical forms by code
        self.pharmaceutical_forms = {
            item.codigo: item for item in self.reference_data.get('pharmaceutical_forms', [])
        }

        # Simplified pharmaceutical forms by code
        self.simplified_forms = {
            item.codigo: item for item in self.reference_data.get('simplified_pharmaceutical_forms', [])
        }

        # Administration routes by code
        self.administration_routes = {
            item.codigo: item for item in self.reference_data.get('administration_routes', [])
        }

        # Excipients by code
        self.excipients = {
            item.codigo: item for item in self.reference_data.get('excipients', [])
        }

        # Package types by code
        self.package_types = {
            item.codigo: item for item in self.reference_data.get('package_types', [])
        }

        # Content units by code
        self.content_units = {
            item.codigo: item for item in self.reference_data.get('content_units', [])
        }

        # Registration statuses by code
        self.registration_statuses = {
            item.codigo: item for item in self.reference_data.get('registration_statuses', [])
        }

        logger.info(f"Built lookup tables: "
                   f"{len(self.active_ingredients)} ingredients, "
                   f"{len(self.laboratories)} labs, "
                   f"{len(self.atc_codes)} ATC codes")

    def transform_drug_for_mongodb(self, drug: Drug) -> Dict:
        """
        Transform a drug object to MongoDB document format with denormalization.

        Args:
            drug: Drug object to transform

        Returns:
            Dictionary ready for MongoDB insertion
        """
        doc = drug.to_dict()

        # Enrich with laboratory names
        if drug.laboratorio_titular:
            lab = self.laboratories.get(drug.laboratorio_titular)
            if lab:
                doc['laboratorio_titular']['nombre'] = lab.nombre

        if drug.laboratorio_comercializador:
            lab = self.laboratories.get(drug.laboratorio_comercializador)
            if lab:
                doc['laboratorio_comercializador']['nombre'] = lab.nombre

        # Enrich package info
        if drug.cod_envase:
            package = self.package_types.get(drug.cod_envase)
            if package:
                doc['envase']['tipo'] = package.nombre

        if drug.unid_contenido:
            unit = self.content_units.get(drug.unid_contenido)
            if unit:
                doc['envase']['unidad_contenido'] = unit.nombre

        # Enrich registration status
        if drug.cod_situacion_registro:
            status = self.registration_statuses.get(drug.cod_situacion_registro)
            if status:
                doc['situacion_registro']['descripcion'] = status.descripcion

        # Enrich pharmaceutical forms
        for i, form in enumerate(drug.formas_farmaceuticas):
            # Form name
            pharm_form = self.pharmaceutical_forms.get(form.codigo)
            if pharm_form:
                doc['formas_farmaceuticas'][i]['nombre'] = pharm_form.nombre

            # Simplified form name
            if form.codigo_simplificado:
                simp_form = self.simplified_forms.get(form.codigo_simplificado)
                if simp_form:
                    doc['formas_farmaceuticas'][i]['nombre_simplificado'] = simp_form.nombre

            # Enrich composition with ingredient names
            for j, comp in enumerate(form.composicion):
                ingredient = self.active_ingredients.get(comp.codigo_principio_activo)
                if ingredient:
                    doc['formas_farmaceuticas'][i]['composicion'][j]['principio_activo'] = {
                        'codigo': comp.codigo_principio_activo,
                        'nombre': ingredient.nombre
                    }

            # Enrich excipient codes with names
            enriched_excipients = []
            for exc_code in form.excipientes:
                excipient = self.excipients.get(exc_code)
                if excipient:
                    enriched_excipients.append({
                        'codigo': exc_code,
                        'nombre': excipient.nombre
                    })
                else:
                    enriched_excipients.append({'codigo': exc_code})
            doc['formas_farmaceuticas'][i]['excipientes'] = enriched_excipients

            # Enrich administration routes with names
            enriched_routes = []
            for route_code in form.vias_administracion:
                route = self.administration_routes.get(route_code)
                if route:
                    enriched_routes.append({
                        'codigo': route_code,
                        'nombre': route.nombre
                    })
                else:
                    enriched_routes.append({'codigo': route_code})
            doc['formas_farmaceuticas'][i]['vias_administracion'] = enriched_routes

        # Enrich ATC with description
        if drug.atc:
            atc_info = self.atc_codes.get(drug.atc.codigo)
            if atc_info:
                doc['atc']['descripcion'] = atc_info.descripcion

        # Add metadata
        doc['metadata'] = {
            'fecha_carga': datetime.utcnow().isoformat(),
            'version_datos': datetime.now().strftime('%Y-%m-%d'),
            'procesado_nlp': False
        }

        return doc

    def extract_interactions_for_mongodb(self, drug: Drug) -> List[Dict]:
        """
        Extract drug interactions as separate documents for the interactions collection.

        Args:
            drug: Drug object

        Returns:
            List of interaction documents
        """
        if not drug.atc or not drug.atc.interacciones:
            return []

        interactions = []
        for interaction in drug.atc.interacciones:
            doc = {
                'medicamento_origen': {
                    'cod_nacion': drug.cod_nacion,
                    'nombre': drug.nombre_comercial,
                    'atc': drug.atc.codigo
                },
                'medicamento_destino': {
                    'atc': interaction.atc_interaccion,
                    'nombre': interaction.descripcion
                },
                'interaccion': {
                    'efecto': interaction.efecto,
                    'recomendacion': interaction.recomendacion,
                    'nlp': {
                        'severidad': None,
                        'tipo': None,
                        'mecanismo': None,
                        'categoria_efecto': None,
                        'procesado': False,
                        'fecha_procesado': None,
                        'confianza': None
                    }
                },
                'bidireccional': True,
                'fecha_carga': datetime.utcnow().isoformat()
            }
            interactions.append(doc)

        return interactions

    def transform_drug_for_neo4j(self, drug: Drug) -> Dict:
        """
        Transform a drug object for Neo4J loading.
        Returns node properties and relationship data.

        Args:
            drug: Drug object

        Returns:
            Dictionary with node properties and relationships
        """
        # Drug node properties
        node = {
            'cod_nacion': drug.cod_nacion,
            'nro_definitivo': drug.nro_definitivo,
            'nombre_comercial': drug.nombre_comercial,
            'presentacion': drug.presentacion,
            'dosificacion': drug.dosificacion,
            'cod_dcsa': drug.cod_dcsa,
            'cod_dcp': drug.cod_dcp,
            'cod_dcpf': drug.cod_dcpf,
            'contenido': drug.contenido,
            'descripcion_contenido': drug.descripcion_contenido,
            'es_psicotropo': drug.es_psicotropo,
            'es_estupefaciente': drug.es_estupefaciente,
            'afecta_conduccion': drug.afecta_conduccion,
            'triangulo_negro': drug.triangulo_negro,
            'requiere_receta': drug.requiere_receta,
            'es_generico': drug.es_generico,
            'es_sustituible': drug.es_sustituible,
            'uso_hospitalario': drug.uso_hospitalario,
            'diagnostico_hospitalario': drug.diagnostico_hospitalario,
            'es_huerfano': drug.es_huerfano,
            'es_biosimilar': drug.es_biosimilar,
            'fecha_autorizacion': drug.fecha_autorizacion,
            'comercializado': drug.comercializado,
            'situacion_registro': self._get_status_name(drug.cod_situacion_registro),
            'url_ficha_tecnica': drug.url_ficha_tecnica,
            'url_prospecto': drug.url_prospecto
        }

        # Relationships
        relationships = {
            'manufactured_by': drug.laboratorio_titular,
            'marketed_by': drug.laboratorio_comercializador,
            'atc_code': drug.atc.codigo if drug.atc else None,
            'contains': [],  # Active ingredients
            'has_form': [],  # Pharmaceutical forms
            'administered_via': [],  # Administration routes
            'contains_excipient': [],  # Excipients
            'packaged_in': drug.cod_envase,
            'interactions': [],  # Drug interactions
            'duplicities': [],  # Therapeutic duplicities
            'biomarkers': []  # Biomarkers
        }

        # Extract ingredients from all pharmaceutical forms
        for form in drug.formas_farmaceuticas:
            if form.codigo not in relationships['has_form']:
                relationships['has_form'].append(form.codigo)

            for route in form.vias_administracion:
                if route not in relationships['administered_via']:
                    relationships['administered_via'].append(route)

            for excipient in form.excipientes:
                if excipient not in relationships['contains_excipient']:
                    relationships['contains_excipient'].append(excipient)

            for comp in form.composicion:
                relationships['contains'].append({
                    'codigo': comp.codigo_principio_activo,
                    'orden': comp.orden,
                    'dosis': comp.dosis,
                    'unidad_dosis': comp.unidad_dosis,
                    'dosis_prescripcion': comp.dosis_prescripcion,
                    'unidad_prescripcion': comp.unidad_prescripcion
                })

        # Extract interactions
        if drug.atc:
            for interaction in drug.atc.interacciones:
                relationships['interactions'].append({
                    'atc_destino': interaction.atc_interaccion,
                    'nombre_destino': interaction.descripcion,
                    'efecto': interaction.efecto,
                    'recomendacion': interaction.recomendacion
                })

            for dup in drug.atc.duplicidades:
                relationships['duplicities'].append({
                    'atc': dup.atc_duplicidad,
                    'descripcion': dup.descripcion,
                    'efecto': dup.efecto,
                    'recomendacion': dup.recomendacion
                })

        # Extract biomarkers
        for bio in drug.biomarcadores:
            relationships['biomarkers'].append({
                'marcador': bio.marcador,
                'clase': bio.clase,
                'genotipo_fenotipo': bio.genotipo_fenotipo,
                'notas': bio.notas
            })

        return {
            'node': node,
            'relationships': relationships
        }

    def _get_status_name(self, code: Optional[int]) -> Optional[str]:
        """Get registration status name by code."""
        if code is None:
            return None
        status = self.registration_statuses.get(code)
        return status.descripcion if status else None

    def transform_reference_for_mongodb(self, collection_name: str) -> List[Dict]:
        """
        Transform reference data for MongoDB.

        Args:
            collection_name: Name of the reference collection

        Returns:
            List of documents ready for MongoDB insertion
        """
        data = self.reference_data.get(collection_name, [])
        return [item.to_dict() for item in data]

    def build_atc_hierarchy(self) -> List[Dict]:
        """
        Build ATC hierarchy relationships for Neo4J.

        Returns:
            List of parent-child relationships
        """
        hierarchy = []
        atc_by_code = {item.codigo: item for item in self.reference_data.get('atc_codes', [])}

        for code, atc in atc_by_code.items():
            # Find parent by removing last character(s)
            parent_code = None
            if len(code) > 1:
                # Try different parent levels
                for length in [len(code) - 1, len(code) - 2, len(code) - 3]:
                    if length >= 1:
                        potential_parent = code[:length]
                        if potential_parent in atc_by_code:
                            parent_code = potential_parent
                            break

            if parent_code:
                hierarchy.append({
                    'parent': parent_code,
                    'child': code
                })

        logger.info(f"Built ATC hierarchy with {len(hierarchy)} relationships")
        return hierarchy
