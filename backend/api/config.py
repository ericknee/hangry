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
    # Session rows older than this are deleted (see api/jobs/retention.py).
    session_retention_days: int = 30

    # Proxies in front of the app that append to X-Forwarded-For: 1 for Cloud Run alone, 2 for
    # Cloudflare -> Cloud Run. Too low shares one bucket among all users; too high lets clients
    # forge their IP. 0 ignores the header. See client_ip in api/ratelimit.py.
    trusted_proxy_count: int = 1

    # Rate limits (see api/ratelimit.py); 0 turns a limit off. "ip" limits are requests per minute
    # per client IP; "session" limits are requests per session over the 30-minute results lifetime.
    # Photos and searches are billed Google requests, so they are the tightest.
    # A group's members each fetch their own photos, often from one shared IP, so these allow
    # 8 devices.
    rate_limit_photo_ip_per_min: int = 120
    rate_limit_photo_session: int = 320
    rate_limit_search_ip_per_min: int = 20
    # Counts failed attempts too (422, 502), so it leaves headroom for retries. A repeat search
    # after a success is served from the cache and costs nothing.
    rate_limit_search_session: int = 10
    rate_limit_session_create_ip_per_min: int = 10
    # Separate buckets: autocomplete fires per keystroke and must not starve the lookup that
    # finishes the location step.
    rate_limit_autocomplete_ip_per_min: int = 60
    rate_limit_city_lookup_ip_per_min: int = 20

    # Group sessions. Friends in one room share an IP, so the per-IP numbers allow up to 8 people.
    # Session limits count failed attempts too.
    rate_limit_join_ip_per_min: int = 10
    rate_limit_join_session: int = 30
    rate_limit_member_edit_ip_per_min: int = 30
    rate_limit_member_edit_session: int = 60
    rate_limit_start_ip_per_min: int = 5
    rate_limit_start_session: int = 5
    rate_limit_votes_ip_per_min: int = 20
    rate_limit_votes_session: int = 40
    rate_limit_end_ip_per_min: int = 10
    rate_limit_end_session: int = 10
    rate_limit_status_ip_per_min: int = 120
    rate_limit_status_session: int = 600
    rate_limit_events_ip_per_min: int = 20
    rate_limit_events_session: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()
