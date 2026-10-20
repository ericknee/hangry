from typing import Annotated

from agent.places_client import PlacesClient
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.db.database import get_db
from api.repositories import sessions_repository
from api.utils.candidate_cache import CandidateCache
from api.utils.event_hub import EventHub
from api.utils.start_guard import StartGuard


def get_places(request: Request) -> PlacesClient:
    """The app-wide PlacesClient created in `main.lifespan`."""
    return request.app.state.places


def get_candidate_cache(request: Request) -> CandidateCache:
    """The app-wide candidate cache created in `main.lifespan`."""
    return request.app.state.candidates


def get_event_hub(request: Request) -> EventHub:
    """The app-wide hub that wakes group event streams, created in `main.lifespan`."""
    return request.app.state.events


def get_start_guard(request: Request) -> StartGuard:
    """The app-wide record of group starts in progress, created in `main.lifespan`."""
    return request.app.state.start_guard


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    """Opens short database sessions; for the event stream, which must not hold one open."""
    return request.app.state.session_factory


async def require_session(session_id: str, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
    """404 unless the session was created, so a per-session limit only ever counts real ids."""
    if await sessions_repository.get_session(db, session_id) is None:
        raise HTTPException(status_code=404, detail="Unknown session")


def require_results(
    session_id: str, cache: Annotated[CandidateCache, Depends(get_candidate_cache)]
) -> None:
    """404 unless the session has cached results (so it exists and has searched, no DB lookup)."""
    if cache.get(session_id) is None:
        raise HTTPException(
            status_code=404, detail="No results for this session; they may have expired"
        )
