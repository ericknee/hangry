import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker

# Settings require these at import time; tests never connect to either service.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("GOOGLE_PLACES_API_KEY", "test-key")

# The shared app is hit many times from one test client; rate limiting is tested on its own apps.
for _name in (
    "PHOTO_IP_PER_MIN",
    "PHOTO_SESSION",
    "SEARCH_IP_PER_MIN",
    "SEARCH_SESSION",
    "SESSION_CREATE_IP_PER_MIN",
    "AUTOCOMPLETE_IP_PER_MIN",
    "CITY_LOOKUP_IP_PER_MIN",
):
    os.environ.setdefault(f"RATE_LIMIT_{_name}", "0")


@pytest.fixture(scope="session")
def pg_url():
    """Fresh schema in the `_test` database, once per run; skips the test if Postgres is down."""
    from pg import prepare_test_database

    try:
        return prepare_test_database()
    except (OSError, RuntimeError) as exc:
        pytest.skip(f"Postgres test database unavailable: {exc}")


@pytest_asyncio.fixture
async def pg_sessions(pg_url):
    """A session factory on the test database, emptied after each test."""
    from pg import new_engine, truncate_all

    engine = new_engine(pg_url)
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await truncate_all(engine)
        await engine.dispose()
