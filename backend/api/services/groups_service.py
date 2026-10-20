"""Group session rules: who can join, when, what a submit does. No HTTP types here.

Every function that depends on the group's state locks the session row first, so concurrent joins,
renames and starts run one at a time. That keeps the member cap and the unique names correct without
retrying on constraint errors. This service owns the transaction: it commits, the repository does
not.
"""

import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime

from agent.places_client import PlacesClient
from agent.search.params import build_search_params
from agent.search.ranking import rank_candidates
from agent.search.retrieval import retrieve_candidates
from agent.types import Candidate
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models import ParticipantRecord, SessionRecord
from api.errors.groups_errors import (
    AlreadySubmitted,
    GroupFull,
    InvalidVotes,
    NotAGroupSession,
    NotAMember,
    NotHost,
    NotInLobby,
    NotSwiping,
    StartInProgress,
)
from api.errors.places_errors import PLACES_ERRORS, describe_error
from api.errors.sessions_errors import (
    ResultsNotFound,
    SearchFailed,
    SessionHasNoLocation,
    SessionNotFound,
)
from api.repositories import groups_repository, sessions_repository
from api.services import sessions_service
from api.types.groups_types import (
    GroupResult,
    GroupStatus,
    MemberOut,
    MeOut,
    VoteIn,
)
from api.types.sessions_types import CreateSessionRequest, SearchRequest
from api.utils.candidate_cache import CandidateCache
from api.utils.group_names import unique_name
from api.utils.group_tally import tally_votes
from api.utils.start_guard import StartGuard

MAX_MEMBERS = 8  # the host included
GROUP_DECK_SIZE = 12  # places a group votes on; a submit must cover all of them


async def _lock_group_session(db: AsyncSession, session_id: str) -> SessionRecord:
    record = await groups_repository.lock_session(db, session_id)
    if record is None:
        raise SessionNotFound(session_id)
    if record.mode != "group":
        raise NotAGroupSession(session_id)
    return record


async def _lock_lobby(db: AsyncSession, session_id: str) -> SessionRecord:
    record = await _lock_group_session(db, session_id)
    if record.phase != "lobby":
        raise NotInLobby(session_id)
    return record


async def _lock_swiping(db: AsyncSession, session_id: str) -> SessionRecord:
    record = await _lock_group_session(db, session_id)
    if record.phase != "swiping":
        raise NotSwiping(session_id)
    return record


def _clean_craving(craving: str | None) -> str | None:
    return (craving or "").strip() or None


async def create_group_session(db: AsyncSession, payload: CreateSessionRequest) -> tuple[str, str]:
    """Create a group session in the lobby with its host, in one transaction. Returns the session
    id and the host's participant id."""
    session_id = str(uuid.uuid4())
    sessions_repository.add_session(
        db,
        SessionRecord(
            id=session_id,
            mode="group",
            phase="lobby",
            state=sessions_service.initial_state(payload),
        ),
    )
    await db.flush()  # the models have no relationship(), so insert the session before its host
    host = await groups_repository.add_member(
        db,
        session_id,
        name=unique_name(payload.name, []),
        craving=_clean_craving(payload.initial_query),
        is_host=True,
    )
    await db.commit()
    return session_id, host.id


async def join(
    db: AsyncSession,
    session_id: str,
    *,
    name: str | None,
    craving: str | None,
    is_host: bool = False,
) -> ParticipantRecord:
    """Add a member to a group session in the lobby."""
    await _lock_lobby(db, session_id)
    taken = await groups_repository.member_names(db, session_id)
    if len(taken) >= MAX_MEMBERS:
        raise GroupFull(session_id)
    member = await groups_repository.add_member(
        db,
        session_id,
        name=unique_name(name, taken),
        craving=_clean_craving(craving),
        is_host=is_host,
    )
    await db.commit()
    return member


async def get_member(db: AsyncSession, session_id: str, participant_id: str) -> ParticipantRecord:
    """The member, or NotAMember. Also the check behind every call that sends a participant id."""
    member = await groups_repository.get_member(db, session_id, participant_id)
    if member is None:
        raise NotAMember(participant_id)
    return member


async def list_members(db: AsyncSession, session_id: str) -> list[ParticipantRecord]:
    return await groups_repository.list_members(db, session_id)


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
    await _lock_lobby(db, session_id)
    member = await get_member(db, session_id, participant_id)
    if name is not None and name.strip():
        others = await groups_repository.member_names(db, session_id, exclude_id=participant_id)
        member.name = unique_name(name, others)
    if craving is not None:
        member.craving = _clean_craving(craving)
    await db.commit()
    return member


async def begin_swiping(db: AsyncSession, session_id: str, setup: dict | None = None) -> None:
    """Lobby -> swiping, recording the host's setup answers. Raises NotInLobby if another start
    got there first."""
    record = await _lock_lobby(db, session_id)
    record.phase = "swiping"
    if setup is not None:
        sessions_repository.set_setup(record, setup)
    await db.commit()


def _partial_key(session_id: str, craving_key: str) -> str:
    return f"{session_id}|{craving_key}"


def _merge(pools: Sequence[Sequence[Candidate]]) -> list[Candidate]:
    """One list with each place once, the first pool's copy winning."""
    seen: set[str] = set()
    merged: list[Candidate] = []
    for pool in pools:
        for candidate in pool:
            if candidate["place_id"] not in seen:
                seen.add(candidate["place_id"])
                merged.append(candidate)
    return merged


async def start(
    db: AsyncSession,
    places: PlacesClient,
    cache: CandidateCache,
    guard: StartGuard,
    session_id: str,
    payload: SearchRequest,
) -> int:
    """Run one Places search per distinct craving, merge the places, and open swiping.

    The phase flips only after every search has succeeded. A search that worked is kept briefly, so
    retrying after a failure pays only for the ones that did not. With no results at all the
    session stays in the lobby so the host can change the setup. Returns the number of places.
    """
    record = await sessions_repository.get_session(db, session_id)
    if record is None:
        raise SessionNotFound(session_id)
    if record.mode != "group":
        raise NotAGroupSession(session_id)
    if record.phase != "lobby":
        raise NotInLobby(session_id)
    location = record.state.get("location")
    if location is None:
        raise SessionHasNoLocation(session_id)
    if not guard.try_acquire(session_id):
        raise StartInProgress(session_id)

    try:
        cravings: dict[str, str] = {}  # lowercased -> as typed; "" is the default search
        for member in await groups_repository.list_members(db, session_id):
            cravings.setdefault((member.craving or "").lower(), member.craving or "")

        pools: list[list[Candidate]] = []
        for key, craving in cravings.items():
            pool = cache.get(_partial_key(session_id, key))
            if pool is None:
                params = build_search_params(
                    after=payload.after,
                    dietary=payload.dietary,
                    craving=craving,
                    price_levels=payload.price_levels,
                    mode=payload.mode,
                    minutes=payload.minutes,
                )
                try:
                    pool = await retrieve_candidates(
                        places, lat=location["lat"], lng=location["lng"], params=params
                    )
                except PLACES_ERRORS as exc:
                    raise SearchFailed(describe_error(exc)) from exc
                cache.set(_partial_key(session_id, key), pool)
            pools.append(pool)

        # Everyone votes on every place, so the deck is the best few of the merged pool.
        merged = rank_candidates(_merge(pools))[:GROUP_DECK_SIZE]
        if merged:
            cache.set(session_id, merged)
            await begin_swiping(db, session_id, payload.model_dump())
        for key in cravings:
            cache.delete(_partial_key(session_id, key))
        return len(merged)
    finally:
        guard.release(session_id)


def deck_place_ids(cache: CandidateCache, session_id: str) -> list[str]:
    """The place ids of the shortlist, best first. ResultsNotFound once the cache has expired."""
    return [r.place_id for r in sessions_service.ranked_restaurants(cache, session_id)]


async def save_votes(
    db: AsyncSession, session_id: str, participant_id: str, votes: Mapping[str, int]
) -> None:
    """Store a member's votes and mark them submitted, in one transaction. The caller has already
    checked that `votes` covers the deck."""
    await _lock_swiping(db, session_id)
    member = await get_member(db, session_id, participant_id)
    if member.submitted_at is not None:
        raise AlreadySubmitted(participant_id)
    groups_repository.add_votes(db, participant_id, votes)
    member.submitted_at = datetime.now(UTC)
    await db.commit()


def _check_deck(votes: Sequence[VoteIn], deck: Sequence[str]) -> dict[str, int]:
    by_place: dict[str, int] = {}
    for vote in votes:
        if vote.place_id in by_place:
            raise InvalidVotes(f"Duplicate vote for {vote.place_id}")
        by_place[vote.place_id] = vote.value
    if set(by_place) != set(deck):
        raise InvalidVotes("Vote on every place in the shortlist")
    return by_place


async def submit_votes(
    db: AsyncSession,
    cache: CandidateCache,
    session_id: str,
    participant_id: str,
    votes: Sequence[VoteIn],
) -> None:
    """A member's one submit: it must cover the whole deck. The last submit decides the winner."""
    by_place = _check_deck(votes, deck_place_ids(cache, session_id))
    await save_votes(db, session_id, participant_id, by_place)
    if await all_submitted(db, session_id):
        await finalize(db, cache, session_id)


async def end_early(db: AsyncSession, session_id: str, place_ids: Sequence[str]) -> None:
    """Submit for every member still swiping, with a 0 (no vote) for each place. Their unsent swipes
    are discarded."""
    await _lock_swiping(db, session_id)
    now = datetime.now(UTC)
    for member in await groups_repository.list_members(db, session_id):
        if member.submitted_at is None:
            groups_repository.add_zero_votes(db, member.id, place_ids)
            member.submitted_at = now
    await db.commit()


async def end_session(
    db: AsyncSession, cache: CandidateCache, session_id: str, participant_id: str
) -> None:
    """The host ends swiping now; whoever has not submitted gets no votes."""
    host = await get_member(db, session_id, participant_id)
    if not host.is_host:
        raise NotHost(participant_id)
    await end_early(db, session_id, deck_place_ids(cache, session_id))
    await finalize(db, cache, session_id)


async def all_submitted(db: AsyncSession, session_id: str) -> bool:
    return await groups_repository.count_unsubmitted(db, session_id) == 0


async def load_votes(db: AsyncSession, session_id: str) -> Sequence[tuple[str, str, int]]:
    return await groups_repository.load_votes(db, session_id)


async def finish(db: AsyncSession, session_id: str, final_pick_place_id: str) -> None:
    """Record the winner and move the session to done. A second call changes nothing."""
    record = await _lock_group_session(db, session_id)
    if record.phase == "done":
        return
    record.phase = "done"
    record.final_pick_place_id = final_pick_place_id
    await db.commit()


async def finalize(db: AsyncSession, cache: CandidateCache, session_id: str) -> None:
    """Count the votes and record the winner."""
    deck = deck_place_ids(cache, session_id)
    tallies = tally_votes(await load_votes(db, session_id), deck)
    await finish(db, session_id, tallies[0].place_id)


async def group_result(
    db: AsyncSession, cache: CandidateCache, record: SessionRecord
) -> GroupResult:
    """The outcome of a finished session. ResultsNotFound if the shortlist has expired."""
    restaurants = sessions_service.ranked_restaurants(cache, record.id)
    tallies = tally_votes(await load_votes(db, record.id), [r.place_id for r in restaurants])
    winner = next(r for r in restaurants if r.place_id == record.final_pick_place_id)
    return GroupResult(
        winner=winner,
        no_likes=all(t.likes == 0 for t in tallies),
        tallies=tallies,
    )


async def group_status(
    db: AsyncSession, cache: CandidateCache, session_id: str, participant_id: str
) -> GroupStatus:
    """Everything one member needs to draw the group screens."""
    record = await sessions_repository.get_session(db, session_id)
    if record is None:
        raise SessionNotFound(session_id)
    if record.mode != "group":
        raise NotAGroupSession(session_id)
    me = await get_member(db, session_id, participant_id)
    members = await groups_repository.list_members(db, session_id)

    result = None
    if record.phase == "done":
        try:
            result = await group_result(db, cache, record)
        except ResultsNotFound:
            result = None  # the shortlist expired; the client shows the session as over
    return GroupStatus(
        phase=record.phase,  # type: ignore[arg-type]
        me=MeOut(
            name=me.name,
            craving=me.craving,
            is_host=me.is_host,
            submitted=me.submitted_at is not None,
        ),
        members=[
            MemberOut(name=m.name, is_host=m.is_host, submitted=m.submitted_at is not None)
            for m in members
        ],
        result=result,
    )
