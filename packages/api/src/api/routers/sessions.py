import uuid

from agent.clients.places import PlacesClient
from agent.graph import build_graph
from agent.state import Candidate
from fastapi import APIRouter, HTTPException

from api.schemas.session import CandidateOut, CreateSessionRequest, SessionResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])

_graph = build_graph()


async def _search_candidates(payload: CreateSessionRequest) -> list[Candidate]:
    assert payload.location is not None
    try:
        client = PlacesClient()
    except KeyError as exc:
        raise HTTPException(status_code=503, detail="Google Places API is not configured") from exc

    radius_m = int((payload.radius_km or 3) * 1000)
    places = await client.search_text(
        payload.initial_query or "restaurants",
        lat=payload.location.lat,
        lng=payload.location.lng,
        radius_m=radius_m,
    )
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
async def create_session(payload: CreateSessionRequest) -> SessionResponse:
    session_id = str(uuid.uuid4())

    candidates: list[Candidate] = []
    if payload.location is not None:
        candidates = await _search_candidates(payload)

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
