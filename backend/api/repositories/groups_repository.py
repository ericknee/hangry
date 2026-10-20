"""Group session persistence: members, votes and the session phase.

Every write that depends on the group's state locks the session row first (`SELECT ... FOR UPDATE`),
so concurrent joins, renames and starts run one at a time. That is what keeps the member cap and
the unique names correct without retrying on constraint errors. Rules about the candidates (does a
submit cover the whole deck, who wins) are not here: they need the cache and live in the service.
"""

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models import ParticipantRecord, SessionRecord, VoteRecord
from api.errors.groups_errors import (
    AlreadySubmitted,
    GroupFull,
    NotAGroupSession,
    NotAMember,
    NotInLobby,
)
from api.errors.sessions_errors import SessionNotFound
from api.utils.group_names import unique_name

MAX_MEMBERS = 8  # the host included


async def _lock_session(db: AsyncSession, session_id: str) -> SessionRecord:
    record = (
        await db.execute(
            select(SessionRecord)
            .where(SessionRecord.id == session_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if record is None:
        raise SessionNotFound(session_id)
    if record.mode != "group":
        raise NotAGroupSession(session_id)
    return record


async def _names(db: AsyncSession, session_id: str, *, exclude_id: str | None = None) -> list[str]:
    query = select(ParticipantRecord.name).where(ParticipantRecord.session_id == session_id)
    if exclude_id is not None:
        query = query.where(ParticipantRecord.id != exclude_id)
    return list((await db.execute(query)).scalars())


async def add_member(
    db: AsyncSession,
    session_id: str,
    *,
    name: str | None,
    craving: str | None,
    is_host: bool,
    commit: bool = True,
) -> ParticipantRecord:
    """Add a member to a group session in the lobby. `commit=False` lets the caller create the
    session and its host in one transaction."""
    record = await _lock_session(db, session_id)
    if record.phase != "lobby":
        raise NotInLobby(session_id)
    taken = await _names(db, session_id)
    if len(taken) >= MAX_MEMBERS:
        raise GroupFull(session_id)

    member = ParticipantRecord(
        session_id=session_id,
        name=unique_name(name, taken),
        craving=(craving or "").strip() or None,
        is_host=is_host,
    )
    db.add(member)
    await (db.commit() if commit else db.flush())
    return member


async def get_member(db: AsyncSession, session_id: str, participant_id: str) -> ParticipantRecord:
    """The member, or NotAMember. Also the check behind every call that sends a participant id."""
    member = await db.get(ParticipantRecord, participant_id)
    if member is None or member.session_id != session_id:
        raise NotAMember(participant_id)
    return member


async def list_members(db: AsyncSession, session_id: str) -> list[ParticipantRecord]:
    """In join order, so the host comes first."""
    result = await db.execute(
        select(ParticipantRecord)
        .where(ParticipantRecord.session_id == session_id)
        .order_by(ParticipantRecord.joined_at, ParticipantRecord.id)
    )
    return list(result.scalars())


async def update_member(
    db: AsyncSession,
    session_id: str,
    participant_id: str,
    *,
    name: str | None,
    craving: str | None,
) -> ParticipantRecord:
    """Lobby edits. A blank `name` or an absent field keeps the current value; a blank `craving`
    clears it."""
    record = await _lock_session(db, session_id)
    if record.phase != "lobby":
        raise NotInLobby(session_id)
    member = await get_member(db, session_id, participant_id)
    if name is not None and name.strip():
        others = await _names(db, session_id, exclude_id=participant_id)
        member.name = unique_name(name, others)
    if craving is not None:
        member.craving = craving.strip() or None
    await db.commit()
    return member


async def begin_swiping(db: AsyncSession, session_id: str) -> None:
    """Lobby -> swiping. Raises NotInLobby if another start got there first."""
    record = await _lock_session(db, session_id)
    if record.phase != "lobby":
        raise NotInLobby(session_id)
    record.phase = "swiping"
    await db.commit()


async def save_votes(
    db: AsyncSession, session_id: str, participant_id: str, votes: Mapping[str, int]
) -> None:
    """Store a member's votes and mark them submitted, in one transaction. The caller has already
    checked that `votes` covers the deck."""
    await _lock_session(db, session_id)
    member = await get_member(db, session_id, participant_id)
    if member.submitted_at is not None:
        raise AlreadySubmitted(participant_id)
    db.add_all(
        VoteRecord(participant_id=participant_id, place_id=place_id, value=value)
        for place_id, value in votes.items()
    )
    member.submitted_at = datetime.now(UTC)
    await db.commit()


async def end_early(db: AsyncSession, session_id: str, place_ids: Sequence[str]) -> None:
    """Submit for every member still swiping, with a 0 (no vote) for each place. Their unsent swipes
    are discarded."""
    await _lock_session(db, session_id)
    now = datetime.now(UTC)
    for member in await list_members(db, session_id):
        if member.submitted_at is not None:
            continue
        db.add_all(
            VoteRecord(participant_id=member.id, place_id=place_id, value=0)
            for place_id in place_ids
        )
        member.submitted_at = now
    await db.commit()


async def all_submitted(db: AsyncSession, session_id: str) -> bool:
    waiting = await db.scalar(
        select(func.count())
        .select_from(ParticipantRecord)
        .where(ParticipantRecord.session_id == session_id)
        .where(ParticipantRecord.submitted_at.is_(None))
    )
    return waiting == 0


async def load_votes(db: AsyncSession, session_id: str) -> list[tuple[str, str, int]]:
    """(member name, place id, value) for every vote in the session, for the tally."""
    result = await db.execute(
        select(ParticipantRecord.name, VoteRecord.place_id, VoteRecord.value)
        .join(VoteRecord, VoteRecord.participant_id == ParticipantRecord.id)
        .where(ParticipantRecord.session_id == session_id)
        .order_by(ParticipantRecord.joined_at, VoteRecord.place_id)
    )
    return [(name, place_id, value) for name, place_id, value in result.all()]


async def finish(db: AsyncSession, session_id: str, final_pick_place_id: str) -> None:
    """Record the winner and move the session to done."""
    record = await _lock_session(db, session_id)
    record.phase = "done"
    record.final_pick_place_id = final_pick_place_id
    await db.commit()
