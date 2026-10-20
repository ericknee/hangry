from typing import Annotated

from agent.places_client import PlacesClient
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import get_db
from api.db.models import SessionRecord
from api.utils.candidate_cache import CandidateCache


def get_places(request: Request) -> PlacesClient:
    """The app-wide PlacesClient created in `main.lifespan`."""
    return request.app.state.places


def get_candidate_cache(request: Request) -> CandidateCache:
    """The app-wide candidate cache created in `main.lifespan`."""
    return request.app.state.candidates


async def require_session(session_id: str, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
    """404 unless the session was created, so a per-session limit only ever counts real ids."""
    if await db.get(SessionRecord, session_id) is None:
        raise HTTPException(status_code=404, detail="Unknown session")


def require_results(
    session_id: str, cache: Annotated[CandidateCache, Depends(get_candidate_cache)]
) -> None:
    """404 unless the session has cached results (so it exists and has searched, no DB lookup)."""
    if cache.get(session_id) is None:
        raise HTTPException(
            status_code=404, detail="No results for this session; they may have expired"
        )
