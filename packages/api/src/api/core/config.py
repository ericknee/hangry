from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Optional while only the Places flow is being exercised: nothing in the API
    # touches the DB or Claude yet. Make these required again once they're wired.
    database_url: str | None = None
    anthropic_api_key: str | None = None
    google_places_api_key: str
    consensus_threshold: float = 0.7
    max_rounds: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()
