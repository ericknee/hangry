"""A real Postgres database for tests that depend on constraints, cascades and row locks.

The database is the dev one's name plus `_test` (or `TEST_DATABASE_URL`), created on first use. The
dev database is never touched: every destructive step checks the name ends in `_test`.
Tests that use it skip when Postgres is unreachable.
"""

import asyncio
import os
from pathlib import Path

import asyncpg
from api.db.models import Base
from dotenv import dotenv_values
from sqlalchemy import text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_database_url() -> URL | None:
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        url = make_url(explicit)
    else:
        dev = dotenv_values(REPO_ROOT / ".env").get("DATABASE_URL")
        if not dev:
            return None
        url = make_url(dev)
        url = url.set(database=f"{url.database}_test")
    if not (url.database or "").endswith("_test"):
        raise RuntimeError(f"Refusing to use {url.database!r} for tests: name must end in _test")
    return url


async def _create_database_if_missing(url: URL) -> None:
    conn = await asyncpg.connect(
        host=url.host,
        port=url.port,
        user=url.username,
        password=url.password,
        database="postgres",
        timeout=3,
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", url.database)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{url.database}"')
    finally:
        await conn.close()


async def _reset_schema(url: URL) -> None:
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    finally:
        await engine.dispose()


def prepare_test_database() -> URL:
    """Create the database and a fresh schema; raises if Postgres is unreachable."""
    url = test_database_url()
    if url is None:
        raise RuntimeError("No DATABASE_URL in .env and no TEST_DATABASE_URL set")
    asyncio.run(_create_database_if_missing(url))
    asyncio.run(_reset_schema(url))
    return url


def new_engine(url: URL) -> AsyncEngine:
    return create_async_engine(url, poolclass=NullPool)


async def truncate_all(engine: AsyncEngine) -> None:
    assert (engine.url.database or "").endswith("_test")
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE votes, participants, sessions CASCADE"))
