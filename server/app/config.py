from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://localhost/praxisdoktor_dev"
    session_secret: str = "dev-only-change-in-production"
    session_cookie_name: str = "praxisdoktor_session"
    session_max_age_hours: int = 168
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    audio_dir: str = "./audio"
    environment: str = "development"

    @property
    def audio_path(self) -> Path:
        p = Path(self.audio_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "+psycopg")


@lru_cache
def get_settings() -> Settings:
    return Settings()
