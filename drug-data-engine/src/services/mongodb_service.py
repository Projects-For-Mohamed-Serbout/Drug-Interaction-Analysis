"""
MongoDB Service Layer.

Provides reusable query methods for the drug interaction database.
Used by the API routes to serve data to the frontend.
"""
from typing import List, Dict, Any, Optional
import logging
import re
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database

logger = logging.getLogger(__name__)


class MongoDBService:
    """Service for querying MongoDB drug interaction data."""

    def __init__(self, uri: str, database: str):
        self.uri = uri
        self.database_name = database
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None

    def connect(self) -> bool:
        try:
            self.client = MongoClient(self.uri)
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            logger.info(f"MongoDBService connected to {self.database_name}")
            return True
        except Exception as e:
            logger.error(f"MongoDBService connection failed: {e}")
            return False

    def disconnect(self):
        if self.client:
            self.client.close()

    # =========================================================================
    # Dashboard
    # =========================================================================
    def get_dashboard_stats(self) -> Dict[str, int]:
        """Get counts for dashboard stat cards."""
        return {
            'medications': self.db['drugs'].count_documents({}),
            'ingredients': self.db['active_ingredients'].count_documents({}),
            'interactions': self.db['drug_interactions'].count_documents({}),
            'laboratories': self.db['laboratories'].count_documents({}),
            'atc_codes': self.db['atc_codes'].count_documents({}),
        }

    # =========================================================================
    # Medications
    # =========================================================================
    def search_medications(self, query: str, limit: int = 50) -> List[Dict]:
        """Search medications by name, cod_nacion, or active ingredient."""
        safe_query = re.escape(query)
        regex = {'$regex': safe_query, '$options': 'i'}

        # Search by name first
        results = list(self.db['drugs'].find(
            {'nombre_comercial': regex},
            {
                'cod_nacion': 1,
                'nombre_comercial': 1,
                'laboratorio_titular.nombre': 1,
                'formas_farmaceuticas.composicion.principio_activo.nombre': 1,
                'formas_farmaceuticas.vias_administracion.nombre': 1,
            }
        ).limit(limit))

        # If few results, also search by cod_nacion
        if len(results) < limit:
            cod_results = list(self.db['drugs'].find(
                {'cod_nacion': regex},
                {
                    'cod_nacion': 1,
                    'nombre_comercial': 1,
                    'laboratorio_titular.nombre': 1,
                    'formas_farmaceuticas.composicion.principio_activo.nombre': 1,
                    'formas_farmaceuticas.vias_administracion.nombre': 1,
                }
            ).limit(limit - len(results)))
            existing_ids = {str(r['_id']) for r in results}
            for r in cod_results:
                if str(r['_id']) not in existing_ids:
                    results.append(r)

        return [self._format_medication(m, query) for m in results]

    def get_medications(
        self, page: int = 1, page_size: int = 20,
        sort_by: str = 'nombre_comercial', sort_order: str = 'asc'
    ) -> Dict:
        """Get paginated list of medications."""
        skip = (page - 1) * page_size
        order = ASCENDING if sort_order == 'asc' else DESCENDING
        total = self.db['drugs'].count_documents({})

        items = list(self.db['drugs'].find(
            {},
            {
                'cod_nacion': 1,
                'nombre_comercial': 1,
                'laboratorio_titular.nombre': 1,
                'formas_farmaceuticas.composicion.principio_activo.nombre': 1,
                'formas_farmaceuticas.vias_administracion.nombre': 1,
                'atc.codigo': 1,
                'comercializado': 1,
            }
        ).sort(sort_by, order).skip(skip).limit(page_size))

        return {
            'items': [self._format_medication(m) for m in items],
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
        }

    def get_medication_by_id(self, cod_nacion: str) -> Optional[Dict]:
        """Get a single medication by cod_nacion."""
        drug = self.db['drugs'].find_one({'cod_nacion': cod_nacion})
        if not drug:
            return None
        drug['_id'] = str(drug['_id'])
        return drug

    # =========================================================================
    # Interactions
    # =========================================================================
    def get_interactions(
        self, page: int = 1, page_size: int = 20,
        severity: Optional[str] = None,
        interaction_type: Optional[str] = None,
    ) -> Dict:
        """Get paginated interactions with optional filters."""
        query = {}
        if severity:
            query['interaccion.nlp.severidad'] = severity
        if interaction_type:
            query['interaccion.nlp.tipo'] = interaction_type

        skip = (page - 1) * page_size
        total = self.db['drug_interactions'].count_documents(query)

        items = list(self.db['drug_interactions'].find(query)
                     .skip(skip).limit(page_size))

        for item in items:
            item['_id'] = str(item['_id'])

        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
        }

    def get_interactions_for_drug(self, cod_nacion: str) -> List[Dict]:
        """Get all interactions for a specific drug."""
        results = list(self.db['drug_interactions'].find(
            {'medicamento_origen.cod_nacion': cod_nacion}
        ))
        for r in results:
            r['_id'] = str(r['_id'])
        return results

    # =========================================================================
    # Active Ingredients
    # =========================================================================
    def get_active_ingredients(
        self, page: int = 1, page_size: int = 20,
        search: Optional[str] = None
    ) -> Dict:
        """Get paginated active ingredients."""
        query = {}
        if search:
            query['nombre'] = {'$regex': re.escape(search), '$options': 'i'}

        skip = (page - 1) * page_size
        total = self.db['active_ingredients'].count_documents(query)

        items = list(self.db['active_ingredients'].find(query)
                     .sort('nombre', ASCENDING).skip(skip).limit(page_size))
        for item in items:
            item['_id'] = str(item['_id'])

        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
        }

    # =========================================================================
    # Laboratories
    # =========================================================================
    def get_laboratories(
        self, page: int = 1, page_size: int = 20,
        search: Optional[str] = None
    ) -> Dict:
        """Get paginated laboratories."""
        query = {}
        if search:
            query['nombre'] = {'$regex': re.escape(search), '$options': 'i'}

        skip = (page - 1) * page_size
        total = self.db['laboratories'].count_documents(query)

        items = list(self.db['laboratories'].find(query)
                     .sort('nombre', ASCENDING).skip(skip).limit(page_size))
        for item in items:
            item['_id'] = str(item['_id'])

        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
        }

    # =========================================================================
    # NLP Analysis
    # =========================================================================
    def get_severity_type_matrix(self) -> Dict:
        """
        Cross-tabulate interaction TYPE x SEVERITY across the processed corpus.
        Powers the "which interaction types carry the most danger" heatmap.
        """
        severity_order = ['contraindicated', 'severe', 'moderate', 'mild', 'unknown']

        rows = list(self.db['drug_interactions'].aggregate([
            {'$match': {
                'interaccion.nlp.tipo': {'$ne': None},
                'interaccion.nlp.severidad': {'$ne': None},
            }},
            {'$group': {
                '_id': {
                    'tipo': '$interaccion.nlp.tipo',
                    'severidad': '$interaccion.nlp.severidad',
                },
                'count': {'$sum': 1},
            }},
        ]))

        # pivot into {type: {severity: count}}
        by_type: Dict[str, Dict[str, int]] = {}
        for r in rows:
            tipo = r['_id'].get('tipo') or 'unknown'
            sev = r['_id'].get('severidad') or 'unknown'
            by_type.setdefault(tipo, {})
            by_type[tipo][sev] = by_type[tipo].get(sev, 0) + r['count']

        types = []
        for tipo, counts in by_type.items():
            total = sum(counts.values())
            types.append({
                'type': tipo,
                'total': total,
                'counts': {s: counts.get(s, 0) for s in severity_order},
            })
        types.sort(key=lambda x: -x['total'])

        return {
            'severities': severity_order,
            'types': types,
            'total': sum(t['total'] for t in types),
        }

    def get_nlp_statistics(self) -> Dict:
        """Get NLP processing statistics and distributions."""
        total = self.db['drug_interactions'].count_documents({})
        processed = self.db['drug_interactions'].count_documents(
            {'interaccion.nlp.procesado': True}
        )

        severity_dist = list(self.db['drug_interactions'].aggregate([
            {'$group': {'_id': '$interaccion.nlp.severidad', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]))

        type_dist = list(self.db['drug_interactions'].aggregate([
            {'$group': {'_id': '$interaccion.nlp.tipo', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]))

        effect_dist = list(self.db['drug_interactions'].aggregate([
            {'$group': {'_id': '$interaccion.nlp.categoria_efecto', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]))

        mechanism_dist = list(self.db['drug_interactions'].aggregate([
            {'$group': {'_id': '$interaccion.nlp.mecanismo', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]))

        avg_confidence = list(self.db['drug_interactions'].aggregate([
            {'$match': {'interaccion.nlp.confianza': {'$exists': True}}},
            {'$group': {'_id': None, 'avg': {'$avg': '$interaccion.nlp.confianza'}}}
        ]))

        return {
            'total_interactions': total,
            'processed': processed,
            'unprocessed': total - processed,
            'processing_rate': round(processed / total * 100, 1) if total > 0 else 0,
            'severity_distribution': [
                {'label': d['_id'] or 'unknown', 'count': d['count']} for d in severity_dist
            ],
            'type_distribution': [
                {'label': d['_id'] or 'unknown', 'count': d['count']} for d in type_dist
            ],
            'effect_category_distribution': [
                {'label': d['_id'] or 'unclassified', 'count': d['count']} for d in effect_dist
            ],
            'mechanism_distribution': [
                {'label': d['_id'] or 'unknown', 'count': d['count']} for d in mechanism_dist
            ],
            'average_confidence': round(avg_confidence[0]['avg'], 3) if avg_confidence else 0,
        }

    # =========================================================================
    # Helpers
    # =========================================================================
    def _format_medication(self, drug: Dict, search_query: str = None) -> Dict:
        """Format a drug document for API response."""
        # Extract first active ingredient
        principio_activo = ''
        via_administracion = ''
        forms = drug.get('formas_farmaceuticas', [])
        if forms:
            comps = forms[0].get('composicion', [])
            if comps:
                pa = comps[0].get('principio_activo', {})
                principio_activo = pa.get('nombre', '') if isinstance(pa, dict) else ''
            vias = forms[0].get('vias_administracion', [])
            if vias:
                via_administracion = vias[0].get('nombre', '')

        matched_by = 'name'
        if search_query:
            cod = drug.get('cod_nacion', '')
            if search_query.lower() in cod.lower():
                matched_by = 'code'

        return {
            'id': str(drug['_id']),
            'codigo_nacional': drug.get('cod_nacion', ''),
            'nombre': drug.get('nombre_comercial', ''),
            'principio_activo': principio_activo,
            'laboratorio': drug.get('laboratorio_titular', {}).get('nombre', ''),
            'via_administracion': via_administracion,
            'matched_by': matched_by,
        }
