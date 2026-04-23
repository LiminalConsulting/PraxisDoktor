from __future__ import annotations
import os
import secrets
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://localhost/praxisdoktor_dev"
    session_secret: str = ""  # loaded from env or generated-and-persisted below
    session_cookie_name: str = "praxisdoktor_session"
    session_max_age_hours: int = 168
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    audio_dir: str = "./audio"
    environment: str = "development"
    data_dir: str = "./var"

    @property
    def audio_path(self) -> Path:
        p = Path(self.audio_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def data_path(self) -> Path:
        p = Path(self.data_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "+psycopg")


def _ensure_session_secret(settings: Settings) -> None:
    """If no SESSION_SECRET was set via env/.env, generate one and persist it
    in var/session_secret.txt so it survives restarts but is never hardcoded."""
    if settings.session_secret:
        return
    secret_file = settings.data_path / "session_secret.txt"
    if secret_file.exists():
        settings.session_secret = secret_file.read_text().strip()
        if settings.session_secret:
            return
    settings.session_secret = secrets.token_hex(32)
    secret_file.write_text(settings.session_secret)
    try:
        os.chmod(secret_file, 0o600)
    except OSError:
        pass  # Windows


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    _ensure_session_secret(s)
    return s
