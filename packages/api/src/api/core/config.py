from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py -> core -> api -> src -> packages/api -> packages -> repo root
REPO_ROOT = Path(__file__).resolve().parents[5]


class Settings(BaseSettings):
    # Absolute, so the repo-root .env is found whatever folder uvicorn/alembic/pytest runs from.
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    database_url: str
    # Optional: nothing in the API uses Claude yet.
    anthropic_api_key: str | None = None
    google_places_api_key: str
    consensus_threshold: float = 0.7
    max_rounds: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()
