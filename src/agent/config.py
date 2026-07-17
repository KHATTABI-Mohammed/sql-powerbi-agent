"""Configuration centralisée de l'agent, chargée depuis les variables d'environnement."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Anthropic (Claude)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"

    # ChromaDB
    chroma_persist_dir: str = str(PROJECT_ROOT / "data" / "chroma")
    chroma_collection_name: str = "schema_docs"

    # SQLite cible
    sqlite_db_path: str = str(PROJECT_ROOT / "data" / "powerbi_sample.db")

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # Agent
    max_sql_retries: int = 2
    rag_top_k: int = 4


settings = Settings()
