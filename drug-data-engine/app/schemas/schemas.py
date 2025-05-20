from pydantic import BaseModel, Field
from typing import Optional


class MedicationSearchResult(BaseModel):
    id: str = Field(..., description="Definitive number (nro_definitivo)")
    codigo_nacional: str = Field(..., description="National code (cod_nacion)")
    nombre: str = Field(..., description="Medication name")
    principio_activo: Optional[str] = Field(None, description="Active substance")
    laboratorio: Optional[str] = Field(None, description="Manufacturing laboratory")
    via_administracion: Optional[str] = Field(None, description="Administration route")
    matched_by: str = Field(..., description="Field that matched the search term")


class ActiveIngredient(BaseModel):
    nombre_principio_activo: str = Field(..., description="Active ingredient name")
    dosis: Optional[str] = Field(None, description="Dosage amount")
    unidad_dosis: Optional[str] = Field(None, description="Dosage unit")
    orden: int = Field(..., description="Order in the composition")


class DuplicityWarning(BaseModel):
    atc_code_description: str = Field(..., description="Description of the ATC code")
    duplicated_atc_description: str = Field(..., description="Description of the duplicated ATC code")
    descripcion: Optional[str] = Field(None, description="Description of the duplicity")
    efecto: Optional[str] = Field(None, description="Effect of the duplicity")
    recomendacion: Optional[str] = Field(None, description="Recommendation for handling the duplicity")


class MedicationDetail(BaseModel):
    id: str = Field(..., description="Definitive number (nro_definitivo)")
    codigo_nacional: str = Field(..., description="National code (cod_nacion)")
    nombre: str = Field(..., description="Medication name")
    contenido: Optional[str] = Field(None, description="Content")
    fecha_autorizacion: Optional[str] = Field(None, description="Authorization date")
    es_generico: Optional[str] = Field(None, description="Is generic medication")
    ficha_tecnica_url: Optional[str] = Field(None, description="URL to technical information")
    laboratorio: Optional[str] = Field(None, description="Manufacturing laboratory")
    sustancia_activa: Optional[str] = Field(None, description="Active substance")
    via_administracion: Optional[str] = Field(None, description="Administration route")
    envase: Optional[str] = Field(None, description="Container type")
    situacion_registro: Optional[str] = Field(None, description="Registration status")
