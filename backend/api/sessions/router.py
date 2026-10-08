from typing import Annotated

from agent.places_client import PlacesClient
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import get_db
from api.deps import get_candidate_cache, get_places
from api.media import stream_upstream
from api.sessions import service
from api.sessions.cache import TTL_SECONDS, CandidateCache
from api.sessions.types import (
    CreateSessionRequest,
    ResultsResponse,
    SearchRequest,
    SearchResponse,
    SessionResponse,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
async def create_session(
    payload: CreateSessionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResponse:
    session_id = await service.create_session(db, payload)
    return SessionResponse(
        session_id=session_id,
        mode=payload.mode,
        share_url=f"/join/{session_id}" if payload.mode == "group" else None,
    )


@router.post("/{session_id}/search", response_model=SearchResponse)
async def search_session(
    session_id: str,
    payload: SearchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    places: Annotated[PlacesClient, Depends(get_places)],
    cache: Annotated[CandidateCache, Depends(get_candidate_cache)],
) -> SearchResponse:
    try:
        count = await service.run_search(db, places, cache, session_id, payload)
    except service.SessionNotFound as exc:
        raise HTTPException(status_code=404, detail="Unknown session") from exc
    except service.SessionHasNoLocation as exc:
        raise HTTPException(
            status_code=400, detail="Session has no location to search around"
        ) from exc
    except service.SearchFailed as exc:
        raise HTTPException(status_code=502, detail=f"Restaurant search failed: {exc}") from exc
    return SearchResponse(count=count)


@router.get("/{session_id}/results", response_model=ResultsResponse)
async def session_results(
    session_id: str,
    cache: Annotated[CandidateCache, Depends(get_candidate_cache)],
) -> ResultsResponse:
    try:
        restaurants = service.ranked_restaurants(cache, session_id)
    except service.ResultsNotFound as exc:
        raise HTTPException(
            status_code=404, detail="No results for this session; they may have expired"
        ) from exc
    return ResultsResponse(restaurants=restaurants)


@router.get("/{session_id}/restaurants/{place_id}/photo", response_class=StreamingResponse)
async def restaurant_photo(
    session_id: str,
    place_id: str,
    places: Annotated[PlacesClient, Depends(get_places)],
    cache: Annotated[CandidateCache, Depends(get_candidate_cache)],
) -> StreamingResponse:
    try:
        upstream = await service.open_photo(places, cache, session_id, place_id)
    except service.PhotoNotFound as exc:
        raise HTTPException(status_code=404, detail="No photo for this restaurant") from exc
    except service.PhotoFetchFailed as exc:
        raise HTTPException(status_code=502, detail=f"Photo fetch failed: {exc}") from exc
    # Photo names expire, so the browser may keep the image no longer than the candidate cache does.
    return stream_upstream(upstream, max_age_s=int(TTL_SECONDS))
