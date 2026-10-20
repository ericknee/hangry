"""Deletes old session rows so coordinates and setup answers aren't kept longer than promised.

The privacy policy says sessions are deleted after 30 days. Run as a one-shot job
(`python -m api.jobs.retention`), e.g. a Cloud Run Job triggered daily by Cloud Scheduler. It is
not a loop inside the API process because Cloud Run pauses CPU between requests, so a background
task there may not run.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.db.database import async_session, engine
from api.db.models import SessionRecord

logger = logging.getLogger(__name__)


async def purge_expired_sessions(
    db: AsyncSession, *, days: int, now: datetime | None = None
) -> int:
    """Delete sessions created more than `days` ago; returns how many were removed."""
    cutoff = (now or datetime.now(UTC)) - timedelta(days=days)
    result = await db.execute(delete(SessionRecord).where(SessionRecord.created_at < cutoff))
    await db.commit()
    return result.rowcount or 0


async def main() -> None:
    """Purge once and exit; a failure propagates so the job run is marked failed and retried."""
    days = get_settings().session_retention_days
    try:
        async with async_session() as db:
            removed = await purge_expired_sessions(db, days=days)
        logger.info("Purged %d sessions older than %d days", removed, days)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
