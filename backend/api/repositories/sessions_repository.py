"""Session rows. Repositories read and write; the service decides and commits."""

from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models import SessionRecord


async def get_session(db: AsyncSession, session_id: str) -> SessionRecord | None:
    return await db.get(SessionRecord, session_id)


def add_session(db: AsyncSession, record: SessionRecord) -> None:
    db.add(record)


def set_setup(record: SessionRecord, setup: dict) -> None:
    """Record the setup answers. The state is reassigned (not mutated) so SQLAlchemy sees the JSON
    column change."""
    record.state = {**record.state, "setup": setup}
