"""
Configuration settings for the Drug Interaction ETL Pipeline.
Loads settings from .env file.
"""
import os
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # Load .env file
        env_path = Path(__file__).parent.parent.parent / '.env'
        load_dotenv(env_path)

        # MongoDB settings
        self.mongodb_uri: str = os.getenv('mongodb_uri', '')
        self.mongodb_db: str = os.getenv('mongodb_db', 'drug_interaction_analysis')

        # Neo4J settings
        self.neo4j_uri: str = os.getenv('neo4j_uri', '')
        self.neo4j_user: str = os.getenv('neo4j_user', 'neo4j')
        self.neo4j_password: str = os.getenv('neo4j_password', '')

        # Data path
        self.data_path: str = os.getenv('data_path', 'data')

        # Environment
        self.env: str = os.getenv('env', 'development')

        # Resolve data path relative to project root
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.data_dir = self.project_root / 'data'

    @property
    def xml_files(self) -> dict:
        """Returns paths to all XML data files."""
        return {
            'prescripcion': self.data_dir / 'Prescripcion.xml',
            'principios_activos': self.data_dir / 'DICCIONARIO_PRINCIPIOS_ACTIVOS.xml',
            'laboratorios': self.data_dir / 'DICCIONARIO_LABORATORIOS.xml',
            'atc': self.data_dir / 'DICCIONARIO_ATC.xml',
            'forma_farmaceutica': self.data_dir / 'DICCIONARIO_FORMA_FARMACEUTICA.xml',
            'forma_farmaceutica_simplificada': self.data_dir / 'DICCIONARIO_FORMA_FARMACEUTICA_SIMPLIFICADAS.xml',
            'vias_administracion': self.data_dir / 'DICCIONARIO_VIAS_ADMINISTRACION.xml',
            'excipientes': self.data_dir / 'DICCIONARIO_EXCIPIENTES_DECL_OBLIGATORIA.xml',
            'envases': self.data_dir / 'DICCIONARIO_ENVASES.xml',
            'situacion_registro': self.data_dir / 'DICCIONARIO_SITUACION_REGISTRO.xml',
            'dcsa': self.data_dir / 'DICCIONARIO_DCSA.xml',
            'dcp': self.data_dir / 'DICCIONARIO_DCP.xml',
            'dcpf': self.data_dir / 'DICCIONARIO_DCPF.xml',
            'unidad_contenido': self.data_dir / 'DICCIONARIO_UNIDAD_CONTENIDO.xml',
        }

    def validate(self) -> bool:
        """Validate that all required settings are present."""
        errors = []

        if not self.mongodb_uri:
            errors.append("MongoDB URI is not configured")
        if not self.neo4j_uri:
            errors.append("Neo4J URI is not configured")
        if not self.neo4j_password:
            errors.append("Neo4J password is not configured")

        # Check if data files exist
        for name, path in self.xml_files.items():
            if not path.exists():
                errors.append(f"XML file not found: {name} at {path}")

        if errors:
            for error in errors:
                print(f"[ERROR] {error}")
            return False

        return True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
