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

    # Rate limits (see api/ratelimit.py); 0 turns a limit off. "ip" limits are requests per minute
    # per client IP; "session" limits are requests per session over the 30-minute results lifetime.
    # Photos and searches are billed Google requests, so they are the tightest.
    rate_limit_photo_ip_per_min: int = 60
    rate_limit_photo_session: int = 40
    rate_limit_search_ip_per_min: int = 5
    rate_limit_search_session: int = 5
    rate_limit_session_create_ip_per_min: int = 10
    rate_limit_places_ip_per_min: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
