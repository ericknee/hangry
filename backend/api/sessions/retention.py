"""Deletes old session rows so coordinates and setup answers aren't kept longer than promised.

The privacy policy says sessions are deleted after 30 days. Runs once at startup and then hourly,
inside the API process: the app already has to run as a single always-on instance because of the
in-memory candidate cache.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.db.models import SessionRecord

logger = logging.getLogger(__name__)

PURGE_INTERVAL_S = 3600


async def purge_expired_sessions(
    db: AsyncSession, *, days: int, now: datetime | None = None
) -> int:
    """Delete sessions created more than `days` ago; returns how many were removed."""
    cutoff = (now or datetime.utcnow()) - timedelta(days=days)  # created_at is naive UTC
    result = await db.execute(delete(SessionRecord).where(SessionRecord.created_at < cutoff))
    await db.commit()
    return result.rowcount or 0


async def run_purge_loop(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    days: int,
    interval_s: int = PURGE_INTERVAL_S,
) -> None:
    """Purge forever; a failed pass (e.g. the database is briefly down) is logged and retried."""
    while True:
        try:
            async with session_factory() as db:
                removed = await purge_expired_sessions(db, days=days)
            if removed:
                logger.info("Purged %d expired sessions", removed)
        except Exception:
            logger.exception("Session purge failed")
        await asyncio.sleep(interval_s)
