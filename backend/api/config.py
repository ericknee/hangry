from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py -> api -> backend -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # Absolute, so the repo-root .env is found whatever folder uvicorn/alembic/pytest runs from.
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    database_url: str
    google_places_api_key: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
