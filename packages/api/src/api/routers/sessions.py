import logging
import uuid
from typing import Annotated

import httpx
from agent.clients.places import PlacesClient
from agent.graph import build_graph
from agent.state import Candidate
from fastapi import APIRouter, Depends

from api.core.places import get_places
from api.schemas.session import CandidateOut, CreateSessionRequest, SessionResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])

_graph = build_graph()

logger = logging.getLogger(__name__)


async def _search_candidates(
    payload: CreateSessionRequest, places_client: PlacesClient
) -> list[Candidate]:
    assert payload.location is not None
    radius_m = int((payload.radius_km or 3) * 1000)
    try:
        places = await places_client.search_text(
            payload.initial_query or "restaurants",
            lat=payload.location.lat,
            lng=payload.location.lng,
            radius_m=radius_m,
        )
    except httpx.HTTPError:
        # Location is optional, so a Places outage shouldn't block starting a session.
        logger.exception("Places search failed; continuing without candidates")
        return []
    # Shaped to seed HangryState["candidates"] once graph invocation (below) is wired.
    return [
        Candidate(
            place_id=p["id"],
            name=p.get("displayName", {}).get("text", ""),
            address=p.get("formattedAddress", ""),
            rating=None,
            price_level=None,
            member_scores={},
            aggregate_score=None,
            reason=None,
        )
        for p in places
    ]


@router.post("", response_model=SessionResponse)
async def create_session(
    payload: CreateSessionRequest,
    places: Annotated[PlacesClient, Depends(get_places)],
) -> SessionResponse:
    session_id = str(uuid.uuid4())

    candidates: list[Candidate] = []
    if payload.location is not None:
        candidates = await _search_candidates(payload, places)

    # TODO Phase 1: persist a SessionRecord row, then invoke `_graph` with an
    # initial HangryState seeded from `candidates` above and `payload`.
    return SessionResponse(
        session_id=session_id,
        mode=payload.mode,
        share_url=f"/join/{session_id}" if payload.mode == "group" else None,
        candidates=[
            CandidateOut(place_id=c["place_id"], name=c["name"], address=c["address"])
            for c in candidates
        ],
    )
