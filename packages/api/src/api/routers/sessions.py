import uuid
from typing import Annotated

import httpx
from agent.clients.places import PlacesClient
from agent.ranking import rank_candidates
from agent.retrieval import retrieve_candidates
from agent.search_params import build_search_params
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.candidate_cache import CandidateCache, get_candidate_cache
from api.core.places import get_places
from api.db.database import get_db
from api.db.models import SessionRecord
from api.schemas.session import (
    CreateSessionRequest,
    RestaurantOut,
    ResultsResponse,
    SearchRequest,
    SearchResponse,
    SessionResponse,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])

# 3 decimals is roughly 110 m: coarse enough to hide the exact spot, fine enough
# that the later search (which reads these stored coordinates) is off by <~80 m.
COORD_DECIMALS = 3


def _initial_state(payload: CreateSessionRequest) -> dict:
    location = payload.location.model_dump() if payload.location else None
    if location:
        location["lat"] = round(location["lat"], COORD_DECIMALS)
        location["lng"] = round(location["lng"], COORD_DECIMALS)
    return {"initial_query": payload.initial_query, "location": location}


@router.post("", response_model=SessionResponse)
async def create_session(
    payload: CreateSessionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResponse:
    session_id = str(uuid.uuid4())

    db.add(SessionRecord(id=session_id, mode=payload.mode, state=_initial_state(payload)))
    await db.commit()

    # No Places search here: it needs the radius, price and dietary answers that
    # come from the question pages, so POST /{session_id}/search runs it instead.
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
    record = await db.get(SessionRecord, session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Unknown session")
    location = record.state.get("location")
    if location is None:
        raise HTTPException(status_code=400, detail="Session has no location to search around")

    params = build_search_params(
        after=payload.after,
        dietary=payload.dietary,
        craving=record.state.get("initial_query", ""),
        price_levels=payload.price_levels,
        mode=payload.mode,
        minutes=payload.minutes,
    )
    try:
        candidates = await retrieve_candidates(
            places, lat=location["lat"], lng=location["lng"], params=params
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Restaurant search failed") from exc

    cache.set(session_id, candidates)
    # Reassigned (not mutated) so SQLAlchemy sees the JSON column change.
    record.state = {**record.state, "setup": payload.model_dump()}
    await db.commit()
    return SearchResponse(count=len(candidates))


@router.get("/{session_id}/results", response_model=ResultsResponse)
async def session_results(
    session_id: str,
    cache: Annotated[CandidateCache, Depends(get_candidate_cache)],
) -> ResultsResponse:
    candidates = cache.get(session_id)
    if candidates is None:
        raise HTTPException(
            status_code=404, detail="No results for this session; they may have expired"
        )
    return ResultsResponse(
        restaurants=[
            RestaurantOut(
                place_id=c["place_id"],
                name=c["name"],
                address=c["address"],
                cuisine=c.get("cuisine"),
                rating=c["rating"],
                rating_count=c.get("rating_count"),
                price_level=c["price_level"],
                distance_m=c.get("distance_m"),
                maps_uri=c.get("maps_uri"),
            )
            for c in rank_candidates(candidates)
        ]
    )


# TODO: update the row with the final pick.
