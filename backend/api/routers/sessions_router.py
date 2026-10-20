from typing import Annotated

from agent.places_client import PlacesClient
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import get_db
from api.deps import get_candidate_cache, get_places, require_results, require_session
from api.ratelimit import rate_limit, session_rate_limit
from api.services import groups_service
from api.services import sessions_service as service
from api.types.places_types import PlaceId
from api.types.sessions_types import (
    CreateSessionRequest,
    ResultsResponse,
    SearchRequest,
    SearchResponse,
    SessionResponse,
)
from api.utils.candidate_cache import CandidateCache
from api.utils.media import stream_upstream

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post(
    "",
    response_model=SessionResponse,
    dependencies=[Depends(rate_limit("session_create", "rate_limit_session_create_ip_per_min"))],
)
async def create_session(
    payload: CreateSessionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResponse:
    participant_id = None
    if payload.mode == "group":
        session_id, participant_id = await groups_service.create_group_session(db, payload)
    else:
        session_id = await service.create_session(db, payload)
    return SessionResponse(
        session_id=session_id,
        mode=payload.mode,
        share_url=f"/join/{session_id}" if payload.mode == "group" else None,
        participant_id=participant_id,
    )


@router.post(
    "/{session_id}/search",
    response_model=SearchResponse,
    dependencies=[
        Depends(rate_limit("search", "rate_limit_search_ip_per_min")),
        Depends(require_session),
        Depends(session_rate_limit("search", "rate_limit_search_session")),
    ],
)
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


@router.get(
    "/{session_id}/restaurants/{place_id}/photo",
    response_class=StreamingResponse,
    dependencies=[
        Depends(rate_limit("photo", "rate_limit_photo_ip_per_min")),
        Depends(require_results),
        Depends(session_rate_limit("photo", "rate_limit_photo_session")),
    ],
)
async def restaurant_photo(
    session_id: str,
    place_id: PlaceId,
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
    return stream_upstream(upstream, max_age_s=int(cache.remaining_seconds(session_id)))
