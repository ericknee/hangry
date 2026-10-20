"""Group session endpoints. The participant id is the credential: REST calls send it in the
`X-Participant-Id` header; the event stream, which a browser opens without custom headers, takes it
as the `participant_id` query parameter."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import contextmanager
from typing import Annotated

from agent.places_client import PlacesClient
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.db.database import get_db
from api.db.models import ParticipantRecord
from api.deps import (
    get_candidate_cache,
    get_event_hub,
    get_places,
    get_session_factory,
    get_start_guard,
    require_session,
)
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
from api.errors.sessions_errors import (
    ResultsNotFound,
    SearchFailed,
    SessionHasNoLocation,
    SessionNotFound,
)
from api.ratelimit import rate_limit, session_rate_limit
from api.services import groups_service
from api.types.groups_types import (
    GroupStatus,
    JoinRequest,
    JoinResponse,
    MeOut,
    SubmitVotesRequest,
    UpdateMemberRequest,
)
from api.types.sessions_types import SearchRequest, SearchResponse
from api.utils.candidate_cache import CandidateCache
from api.utils.event_hub import CLOSED, EventHub
from api.utils.start_guard import StartGuard

router = APIRouter(prefix="/sessions", tags=["groups"])

KEEPALIVE_SECONDS = 15  # proxies drop streams that stay silent for too long

# Domain error -> (status code, message). A None message means "use the error's own text".
_ERRORS: dict[type[Exception], tuple[int, str | None]] = {
    SessionNotFound: (404, "Unknown session"),
    NotAGroupSession: (404, "Not a group session"),
    NotInLobby: (409, "The session has already started"),
    GroupFull: (409, "This session is full"),
    AlreadySubmitted: (409, "You already submitted your votes"),
    NotSwiping: (409, "Swiping is not open"),
    NotHost: (403, "Only the host can do that"),
    NotAMember: (403, "Not a member of this session"),
    InvalidVotes: (400, None),
    ResultsNotFound: (404, "The shortlist has expired; start a new session"),
    SessionHasNoLocation: (400, "Session has no location to search around"),
    StartInProgress: (409, "The host is starting the search"),
}


@contextmanager
def domain_errors():
    """Turn the service's domain errors into HTTP errors."""
    try:
        yield
    except tuple(_ERRORS) as exc:
        status, message = _ERRORS[type(exc)]
        raise HTTPException(status_code=status, detail=message or str(exc)) from exc


async def require_member(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_participant_id: Annotated[str | None, Header()] = None,
) -> ParticipantRecord:
    if not x_participant_id:
        raise HTTPException(status_code=401, detail="Missing participant id")
    with domain_errors():
        return await groups_service.get_member(db, session_id, x_participant_id)


async def require_stream_member(
    session_id: str,
    participant_id: Annotated[str, Query()],
    factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> None:
    """Checks the credential in its own short session: the stream must not hold a connection."""
    async with factory() as db:
        with domain_errors():
            await groups_service.get_member(db, session_id, participant_id)


def reject_while_starting(
    session_id: str, guard: Annotated[StartGuard, Depends(get_start_guard)]
) -> None:
    """Members and cravings are frozen while the host's searches run."""
    if guard.is_active(session_id):
        raise HTTPException(status_code=409, detail=_ERRORS[StartInProgress][1])


Member = Annotated[ParticipantRecord, Depends(require_member)]
Db = Annotated[AsyncSession, Depends(get_db)]
Cache = Annotated[CandidateCache, Depends(get_candidate_cache)]
Hub = Annotated[EventHub, Depends(get_event_hub)]


@router.post(
    "/{session_id}/join",
    response_model=JoinResponse,
    dependencies=[
        Depends(rate_limit("join", "rate_limit_join_ip_per_min")),
        Depends(require_session),
        Depends(session_rate_limit("join", "rate_limit_join_session")),
        Depends(reject_while_starting),
    ],
)
async def join_session(session_id: str, payload: JoinRequest, db: Db, hub: Hub) -> JoinResponse:
    with domain_errors():
        member = await groups_service.join(
            db, session_id, name=payload.name, craving=payload.craving
        )
    hub.notify(session_id)
    return JoinResponse(participant_id=member.id, name=member.name)


@router.patch(
    "/{session_id}/me",
    response_model=MeOut,
    dependencies=[
        Depends(rate_limit("member_edit", "rate_limit_member_edit_ip_per_min")),
        Depends(require_session),
        Depends(session_rate_limit("member_edit", "rate_limit_member_edit_session")),
        Depends(reject_while_starting),
    ],
)
async def update_me(
    session_id: str, payload: UpdateMemberRequest, member: Member, db: Db, hub: Hub
) -> MeOut:
    with domain_errors():
        updated = await groups_service.update_member(
            db, session_id, member.id, name=payload.name, craving=payload.craving
        )
    hub.notify(session_id)
    return MeOut(
        name=updated.name,
        craving=updated.craving,
        is_host=updated.is_host,
        submitted=updated.submitted_at is not None,
    )


@router.get(
    "/{session_id}/group",
    response_model=GroupStatus,
    dependencies=[
        Depends(rate_limit("status", "rate_limit_status_ip_per_min")),
        Depends(require_session),
        Depends(session_rate_limit("status", "rate_limit_status_session")),
    ],
)
async def group_status(session_id: str, member: Member, db: Db, cache: Cache) -> GroupStatus:
    """The same snapshot the event stream pushes; the fallback after a reconnect or a refocus."""
    with domain_errors():
        return await groups_service.group_status(db, cache, session_id, member.id)


@router.get(
    "/{session_id}/events",
    response_class=StreamingResponse,
    dependencies=[
        Depends(rate_limit("events", "rate_limit_events_ip_per_min")),
        Depends(require_stream_member),
        Depends(session_rate_limit("events", "rate_limit_events_session")),
    ],
)
async def group_events(
    session_id: str,
    participant_id: Annotated[str, Query()],
    factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
    cache: Cache,
    hub: Hub,
) -> StreamingResponse:
    return StreamingResponse(
        _event_stream(factory, cache, hub, session_id, participant_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _event_stream(
    factory: async_sessionmaker[AsyncSession],
    cache: CandidateCache,
    hub: EventHub,
    session_id: str,
    participant_id: str,
) -> AsyncIterator[str]:
    """A `status` event now and after every change; a comment line when quiet. Each snapshot is read
    with a short database session, never one held for the life of the stream."""
    queue = hub.subscribe(session_id, participant_id)
    try:
        yield "retry: 3000\n\n"
        while True:
            try:
                async with factory() as db:
                    status = await groups_service.group_status(
                        db, cache, session_id, participant_id
                    )
            except (SessionNotFound, NotAMember, NotAGroupSession):
                return
            yield f"event: status\ndata: {status.model_dump_json()}\n\n"
            while True:
                try:
                    signal = await asyncio.wait_for(queue.get(), timeout=KEEPALIVE_SECONDS)
                except TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                if signal is CLOSED:
                    return
                break
    finally:
        hub.unsubscribe(session_id, participant_id, queue)


@router.post(
    "/{session_id}/start",
    response_model=SearchResponse,
    dependencies=[
        Depends(rate_limit("start", "rate_limit_start_ip_per_min")),
        Depends(require_session),
        Depends(session_rate_limit("start", "rate_limit_start_session")),
    ],
)
async def start_session(
    session_id: str,
    payload: SearchRequest,
    member: Member,
    db: Db,
    places: Annotated[PlacesClient, Depends(get_places)],
    cache: Cache,
    guard: Annotated[StartGuard, Depends(get_start_guard)],
    hub: Hub,
) -> SearchResponse:
    """Host only. Zero places leaves the session in the lobby so the host can change the setup."""
    if not member.is_host:
        raise HTTPException(status_code=403, detail=_ERRORS[NotHost][1])
    try:
        with domain_errors():
            count = await groups_service.start(db, places, cache, guard, session_id, payload)
    except SearchFailed as exc:
        raise HTTPException(status_code=502, detail=f"Restaurant search failed: {exc}") from exc
    hub.notify(session_id)
    return SearchResponse(count=count)


@router.post(
    "/{session_id}/votes",
    response_model=GroupStatus,
    dependencies=[
        Depends(rate_limit("votes", "rate_limit_votes_ip_per_min")),
        Depends(require_session),
        Depends(session_rate_limit("votes", "rate_limit_votes_session")),
    ],
)
async def submit_votes(
    session_id: str, payload: SubmitVotesRequest, member: Member, db: Db, cache: Cache, hub: Hub
) -> GroupStatus:
    with domain_errors():
        await groups_service.submit_votes(db, cache, session_id, member.id, payload.votes)
        status = await groups_service.group_status(db, cache, session_id, member.id)
    hub.notify(session_id)
    return status


@router.post(
    "/{session_id}/end",
    response_model=GroupStatus,
    dependencies=[
        Depends(rate_limit("end", "rate_limit_end_ip_per_min")),
        Depends(require_session),
        Depends(session_rate_limit("end", "rate_limit_end_session")),
    ],
)
async def end_session(
    session_id: str, member: Member, db: Db, cache: Cache, hub: Hub
) -> GroupStatus:
    """Host only: submit for everyone still swiping (no votes) and show the result."""
    with domain_errors():
        await groups_service.end_session(db, cache, session_id, member.id)
        status = await groups_service.group_status(db, cache, session_id, member.id)
    hub.notify(session_id)
    return status
