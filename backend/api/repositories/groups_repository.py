"""Group session queries and writes: members and votes.

No rules and no commits here. The service decides what is allowed and owns the transaction; this
module only reads and writes rows. `lock_session` takes the row lock the service relies on to run
concurrent joins, renames and starts one at a time.
"""

from collections.abc import Iterable, Mapping, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models import ParticipantRecord, SessionRecord, VoteRecord


async def lock_session(db: AsyncSession, session_id: str) -> SessionRecord | None:
    """`SELECT ... FOR UPDATE` on the session row, held until the transaction ends."""
    result = await db.execute(
        select(SessionRecord)
        .where(SessionRecord.id == session_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    return result.scalar_one_or_none()


async def member_names(
    db: AsyncSession, session_id: str, *, exclude_id: str | None = None
) -> list[str]:
    query = select(ParticipantRecord.name).where(ParticipantRecord.session_id == session_id)
    if exclude_id is not None:
        query = query.where(ParticipantRecord.id != exclude_id)
    return list((await db.execute(query)).scalars())


async def get_member(
    db: AsyncSession, session_id: str, participant_id: str
) -> ParticipantRecord | None:
    """None if there is no such member, or the member belongs to another session."""
    member = await db.get(ParticipantRecord, participant_id)
    return member if member is not None and member.session_id == session_id else None


async def list_members(db: AsyncSession, session_id: str) -> list[ParticipantRecord]:
    """In join order, so the host comes first."""
    result = await db.execute(
        select(ParticipantRecord)
        .where(ParticipantRecord.session_id == session_id)
        .order_by(ParticipantRecord.joined_at, ParticipantRecord.id)
    )
    return list(result.scalars())


async def count_unsubmitted(db: AsyncSession, session_id: str) -> int:
    count = await db.scalar(
        select(func.count())
        .select_from(ParticipantRecord)
        .where(ParticipantRecord.session_id == session_id)
        .where(ParticipantRecord.submitted_at.is_(None))
    )
    return count or 0


async def add_member(
    db: AsyncSession,
    session_id: str,
    *,
    name: str,
    craving: str | None,
    is_host: bool,
) -> ParticipantRecord:
    member = ParticipantRecord(session_id=session_id, name=name, craving=craving, is_host=is_host)
    db.add(member)
    await db.flush()
    return member


def add_votes(db: AsyncSession, participant_id: str, votes: Mapping[str, int]) -> None:
    db.add_all(
        VoteRecord(participant_id=participant_id, place_id=place_id, value=value)
        for place_id, value in votes.items()
    )


def add_zero_votes(db: AsyncSession, participant_id: str, place_ids: Iterable[str]) -> None:
    add_votes(db, participant_id, dict.fromkeys(place_ids, 0))


async def load_votes(db: AsyncSession, session_id: str) -> Sequence[tuple[str, str, int]]:
    """(member name, place id, value) for every vote in the session, for the tally."""
    result = await db.execute(
        select(ParticipantRecord.name, VoteRecord.place_id, VoteRecord.value)
        .join(VoteRecord, VoteRecord.participant_id == ParticipantRecord.id)
        .where(ParticipantRecord.session_id == session_id)
        .order_by(ParticipantRecord.joined_at, VoteRecord.place_id)
    )
    return [(name, place_id, value) for name, place_id, value in result.all()]
