from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    anthropic_api_key: str
    google_places_api_key: str
    consensus_threshold: float = 0.7
    max_rounds: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()
