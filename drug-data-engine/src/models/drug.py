"""
Data models for drug entities.
These models represent the structure of data extracted from CIMA XML files.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import date


@dataclass
class ActiveIngredient:
    """Active ingredient (Principio Activo)."""
    codigo: int
    codigo_aemps: str
    nombre: str
    lista_psicotropo: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'codigo': self.codigo,
            'codigo_aemps': self.codigo_aemps,
            'nombre': self.nombre,
            'lista_psicotropo': self.lista_psicotropo
        }


@dataclass
class Laboratory:
    """Laboratory/Manufacturer."""
    codigo: int
    nombre: str
    direccion: Optional[str] = None
    codigo_postal: Optional[str] = None
    localidad: Optional[str] = None
    cif: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'codigo': self.codigo,
            'nombre': self.nombre,
            'direccion': self.direccion,
            'codigo_postal': self.codigo_postal,
            'localidad': self.localidad,
            'cif': self.cif
        }


@dataclass
class ATCCode:
    """ATC Classification Code."""
    nro: int
    codigo: str
    descripcion: str

    def to_dict(self) -> dict:
        return {
            'nro': self.nro,
            'codigo': self.codigo,
            'descripcion': self.descripcion
        }


@dataclass
class PharmaceuticalForm:
    """Pharmaceutical Form (Forma Farmacéutica)."""
    codigo: int
    nombre: str
    codigo_simplificado: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            'codigo': self.codigo,
            'nombre': self.nombre,
            'codigo_simplificado': self.codigo_simplificado
        }


@dataclass
class AdministrationRoute:
    """Administration Route (Vía de Administración)."""
    codigo: int
    nombre: str

    def to_dict(self) -> dict:
        return {
            'codigo': self.codigo,
            'nombre': self.nombre
        }


@dataclass
class Excipient:
    """Excipient with mandatory declaration."""
    codigo: int
    nombre: str

    def to_dict(self) -> dict:
        return {
            'codigo': self.codigo,
            'nombre': self.nombre
        }


@dataclass
class PackageType:
    """Package Type (Envase)."""
    codigo: int
    nombre: str

    def to_dict(self) -> dict:
        return {
            'codigo': self.codigo,
            'nombre': self.nombre
        }


@dataclass
class ContentUnit:
    """Content Unit (Unidad de Contenido)."""
    codigo: int
    nombre: str

    def to_dict(self) -> dict:
        return {
            'codigo': self.codigo,
            'nombre': self.nombre
        }


@dataclass
class RegistrationStatus:
    """Registration Status (Situación de Registro)."""
    codigo: int
    descripcion: str

    def to_dict(self) -> dict:
        return {
            'codigo': self.codigo,
            'descripcion': self.descripcion
        }


@dataclass
class DCSA:
    """SNOMED CT Substance Code."""
    codigo: str
    nombre: str

    def to_dict(self) -> dict:
        return {
            'codigo': self.codigo,
            'nombre': self.nombre
        }


@dataclass
class DCP:
    """SNOMED CT Clinical Drug Code."""
    codigo: str
    nombre: str
    codigo_dcsa: str

    def to_dict(self) -> dict:
        return {
            'codigo': self.codigo,
            'nombre': self.nombre,
            'codigo_dcsa': self.codigo_dcsa
        }


@dataclass
class DCPF:
    """SNOMED CT Clinical Drug + Form Code."""
    codigo: str
    nombre: str
    codigo_dcp: str

    def to_dict(self) -> dict:
        return {
            'codigo': self.codigo,
            'nombre': self.nombre,
            'codigo_dcp': self.codigo_dcp
        }


@dataclass
class DrugComposition:
    """Drug composition with active ingredient and dosage."""
    codigo_principio_activo: int
    orden: int
    dosis: Optional[float] = None
    unidad_dosis: Optional[str] = None
    dosis_composicion: Optional[float] = None
    unidad_composicion: Optional[str] = None
    dosis_administracion: Optional[float] = None
    unidad_administracion: Optional[str] = None
    dosis_prescripcion: Optional[str] = None
    unidad_prescripcion: Optional[str] = None
    cantidad_volumen: Optional[float] = None
    unidad_volumen: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'codigo_principio_activo': self.codigo_principio_activo,
            'orden': self.orden,
            'dosis': self.dosis,
            'unidad_dosis': self.unidad_dosis,
            'dosis_composicion': self.dosis_composicion,
            'unidad_composicion': self.unidad_composicion,
            'dosis_administracion': self.dosis_administracion,
            'unidad_administracion': self.unidad_administracion,
            'dosis_prescripcion': self.dosis_prescripcion,
            'unidad_prescripcion': self.unidad_prescripcion,
            'cantidad_volumen': self.cantidad_volumen,
            'unidad_volumen': self.unidad_volumen
        }


@dataclass
class DrugInteraction:
    """Drug interaction information."""
    atc_interaccion: str
    descripcion: str
    efecto: str
    recomendacion: str
    # NLP fields (to be filled later)
    severidad: Optional[str] = None
    tipo: Optional[str] = None
    mecanismo: Optional[str] = None
    categoria_efecto: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'atc_interaccion': self.atc_interaccion,
            'descripcion': self.descripcion,
            'efecto': self.efecto,
            'recomendacion': self.recomendacion,
            'nlp': {
                'severidad': self.severidad,
                'tipo': self.tipo,
                'mecanismo': self.mecanismo,
                'categoria_efecto': self.categoria_efecto,
                'procesado': False
            }
        }


@dataclass
class Duplicity:
    """Therapeutic duplicity warning."""
    atc_duplicidad: str
    descripcion: str
    efecto: str
    recomendacion: str

    def to_dict(self) -> dict:
        return {
            'atc_duplicidad': self.atc_duplicidad,
            'descripcion': self.descripcion,
            'efecto': self.efecto,
            'recomendacion': self.recomendacion
        }


@dataclass
class GeriatricWarning:
    """Geriatric warning."""
    alerta: str
    riesgo: str
    recomendacion: str

    def to_dict(self) -> dict:
        return {
            'alerta': self.alerta,
            'riesgo': self.riesgo,
            'recomendacion': self.recomendacion
        }


@dataclass
class Biomarker:
    """Biomarker/pharmacogenomic marker."""
    clase: str
    marcador: str
    genotipo_fenotipo: Optional[str] = None
    secciones_ft: Optional[str] = None
    descripcion: Optional[str] = None
    inclusion_sns: bool = False
    notas: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'clase': self.clase,
            'marcador': self.marcador,
            'genotipo_fenotipo': self.genotipo_fenotipo,
            'secciones_ft': self.secciones_ft.split('|') if self.secciones_ft else [],
            'descripcion': self.descripcion,
            'inclusion_sns': self.inclusion_sns,
            'notas': self.notas
        }


@dataclass
class SupplyProblem:
    """Supply problem information."""
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    observaciones: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'fecha_inicio': self.fecha_inicio,
            'fecha_fin': self.fecha_fin,
            'observaciones': self.observaciones
        }


@dataclass
class DrugPharmaceuticalForm:
    """Pharmaceutical form for a drug with composition."""
    codigo: int
    codigo_simplificado: Optional[int] = None
    numero_principios_activos: int = 0
    composicion: List[DrugComposition] = field(default_factory=list)
    excipientes: List[int] = field(default_factory=list)
    vias_administracion: List[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'codigo': self.codigo,
            'codigo_simplificado': self.codigo_simplificado,
            'numero_principios_activos': self.numero_principios_activos,
            'composicion': [c.to_dict() for c in self.composicion],
            'excipientes': self.excipientes,
            'vias_administracion': self.vias_administracion
        }


@dataclass
class DrugATC:
    """ATC information for a drug including interactions."""
    codigo: str
    teratogenia: Optional[str] = None
    interacciones: List[DrugInteraction] = field(default_factory=list)
    duplicidades: List[Duplicity] = field(default_factory=list)
    alertas_geriatria: List[GeriatricWarning] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'codigo': self.codigo,
            'teratogenia': self.teratogenia,
            'interacciones': [i.to_dict() for i in self.interacciones],
            'duplicidades': [d.to_dict() for d in self.duplicidades],
            'alertas_geriatria': [a.to_dict() for a in self.alertas_geriatria]
        }


@dataclass
class Drug:
    """Main Drug/Medication entity."""
    # Primary identifiers
    cod_nacion: str
    nro_definitivo: str

    # Names
    nombre_comercial: str
    presentacion: str
    dosificacion: Optional[str] = None

    # SNOMED codes
    cod_dcsa: Optional[str] = None
    cod_dcp: Optional[str] = None
    cod_dcpf: Optional[str] = None

    # Package info
    cod_envase: Optional[int] = None
    contenido: Optional[int] = None
    unid_contenido: Optional[int] = None
    descripcion_contenido: Optional[str] = None

    # Classification flags
    es_psicotropo: bool = False
    es_estupefaciente: bool = False
    afecta_conduccion: bool = False
    triangulo_negro: bool = False
    requiere_receta: bool = False
    es_generico: bool = False
    es_sustituible: bool = False
    envase_clinico: bool = False
    uso_hospitalario: bool = False
    diagnostico_hospitalario: bool = False
    tratamiento_larga_duracion: bool = False
    control_medico_especial: bool = False
    es_huerfano: bool = False
    base_plantas: bool = False
    es_biosimilar: bool = False
    importacion_paralela: bool = False
    es_radiofarmaco: bool = False
    serializacion: bool = False
    tiene_excipientes_obligatorios: bool = False

    # Laboratory references
    laboratorio_titular: Optional[int] = None
    laboratorio_comercializador: Optional[int] = None

    # Dates
    fecha_autorizacion: Optional[str] = None
    fecha_comercializacion: Optional[str] = None
    fecha_situacion_registro: Optional[str] = None

    # Status
    comercializado: bool = False
    cod_situacion_registro: Optional[int] = None

    # URLs
    url_ficha_tecnica: Optional[str] = None
    url_prospecto: Optional[str] = None

    # Nested structures
    formas_farmaceuticas: List[DrugPharmaceuticalForm] = field(default_factory=list)
    atc: Optional[DrugATC] = None
    biomarcadores: List[Biomarker] = field(default_factory=list)
    problemas_suministro: List[SupplyProblem] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to MongoDB document format."""
        return {
            'cod_nacion': self.cod_nacion,
            'nro_definitivo': self.nro_definitivo,
            'nombre_comercial': self.nombre_comercial,
            'presentacion': self.presentacion,
            'dosificacion': self.dosificacion,
            'snomed': {
                'dcsa': self.cod_dcsa,
                'dcp': self.cod_dcp,
                'dcpf': self.cod_dcpf
            },
            'envase': {
                'codigo': self.cod_envase,
                'contenido': self.contenido,
                'unidad_contenido_codigo': self.unid_contenido,
                'descripcion': self.descripcion_contenido
            },
            'clasificacion': {
                'psicotropo': self.es_psicotropo,
                'estupefaciente': self.es_estupefaciente,
                'afecta_conduccion': self.afecta_conduccion,
                'triangulo_negro': self.triangulo_negro,
                'requiere_receta': self.requiere_receta,
                'generico': self.es_generico,
                'sustituible': self.es_sustituible,
                'envase_clinico': self.envase_clinico,
                'uso_hospitalario': self.uso_hospitalario,
                'diagnostico_hospitalario': self.diagnostico_hospitalario,
                'tratamiento_larga_duracion': self.tratamiento_larga_duracion,
                'control_medico_especial': self.control_medico_especial,
                'huerfano': self.es_huerfano,
                'base_plantas': self.base_plantas,
                'biosimilar': self.es_biosimilar,
                'importacion_paralela': self.importacion_paralela,
                'radiofarmaco': self.es_radiofarmaco,
                'serializacion': self.serializacion,
                'tiene_excipientes_obligatorios': self.tiene_excipientes_obligatorios
            },
            'laboratorio_titular': {'codigo': self.laboratorio_titular},
            'laboratorio_comercializador': {'codigo': self.laboratorio_comercializador},
            'fechas': {
                'autorizacion': self.fecha_autorizacion,
                'comercializacion': self.fecha_comercializacion,
                'situacion_registro': self.fecha_situacion_registro
            },
            'comercializado': self.comercializado,
            'situacion_registro': {'codigo': self.cod_situacion_registro},
            'documentos': {
                'ficha_tecnica': self.url_ficha_tecnica,
                'prospecto': self.url_prospecto
            },
            'formas_farmaceuticas': [f.to_dict() for f in self.formas_farmaceuticas],
            'atc': self.atc.to_dict() if self.atc else None,
            'biomarcadores': [b.to_dict() for b in self.biomarcadores],
            'problemas_suministro': [p.to_dict() for p in self.problemas_suministro]
        }
