from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py -> api -> backend -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # Absolute, so the repo-root .env is found whatever folder uvicorn/alembic/pytest runs from.
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    database_url: str
    google_places_api_key: str
    # "prod" turns off the interactive API docs and the /openapi.json route.
    environment: Literal["dev", "prod"] = "dev"
    # Folder with the built frontend (client/dist). Unset in dev, where Vite serves the pages.
    static_dir: Path | None = None
    # Session rows older than this are deleted (see api/sessions/retention.py).
    session_retention_days: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
