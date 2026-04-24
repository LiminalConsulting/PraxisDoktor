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
    # Shared secret the public website (Cloudflare Pages) sends with every
    # /api/public/* request. Generated-and-persisted on first run, like session_secret.
    public_api_key: str = ""

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


def _ensure_persisted_secret(settings: Settings, attr: str, filename: str) -> None:
    if getattr(settings, attr):
        return
    secret_file = settings.data_path / filename
    if secret_file.exists():
        val = secret_file.read_text().strip()
        if val:
            setattr(settings, attr, val)
            return
    val = secrets.token_hex(32)
    setattr(settings, attr, val)
    secret_file.write_text(val)
    try:
        os.chmod(secret_file, 0o600)
    except OSError:
        pass  # Windows


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    _ensure_persisted_secret(s, "session_secret", "session_secret.txt")
    _ensure_persisted_secret(s, "public_api_key", "public_api_key.txt")
    return s
