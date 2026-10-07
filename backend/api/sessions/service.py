"""Session business logic. No HTTP types here: the router maps these errors to status codes."""

import uuid

import httpx
from agent.places_client import PlacesClient
from agent.search.params import build_search_params
from agent.search.ranking import rank_candidates
from agent.search.retrieval import retrieve_candidates
from agent.types import Candidate
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models import SessionRecord
from api.sessions.cache import CandidateCache
from api.sessions.types import CreateSessionRequest, RestaurantOut, SearchRequest

# 3 decimals is roughly 110 m: coarse enough to hide the exact spot, fine enough
# that the search (which reads these stored coordinates) is off by <~80 m.
COORD_DECIMALS = 3


class SessionNotFound(Exception):
    pass


class SessionHasNoLocation(Exception):
    pass


class SearchFailed(Exception):
    """The Places search errored out (network failure, bad key, quota)."""


class ResultsNotFound(Exception):
    """No cached results for the session: never searched, expired, or the server restarted."""


def _initial_state(payload: CreateSessionRequest) -> dict:
    location = payload.location.model_dump() if payload.location else None
    if location:
        location["lat"] = round(location["lat"], COORD_DECIMALS)
        location["lng"] = round(location["lng"], COORD_DECIMALS)
    return {"initial_query": payload.initial_query, "location": location}


async def create_session(db: AsyncSession, payload: CreateSessionRequest) -> str:
    """Record a new session and return its id. It does not search: the search needs the setup
    answers that come later, so `run_search` does it."""
    session_id = str(uuid.uuid4())
    db.add(SessionRecord(id=session_id, mode=payload.mode, state=_initial_state(payload)))
    await db.commit()
    return session_id


async def run_search(
    db: AsyncSession,
    places: PlacesClient,
    cache: CandidateCache,
    session_id: str,
    payload: SearchRequest,
) -> int:
    """Run the one Places search for a session, cache the candidates, record the setup answers."""
    record = await db.get(SessionRecord, session_id)
    if record is None:
        raise SessionNotFound(session_id)
    location = record.state.get("location")
    if location is None:
        raise SessionHasNoLocation(session_id)

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
        raise SearchFailed(session_id) from exc

    cache.set(session_id, candidates)
    # Reassigned (not mutated) so SQLAlchemy sees the JSON column change.
    record.state = {**record.state, "setup": payload.model_dump()}
    await db.commit()
    return len(candidates)


def _to_restaurant(c: Candidate) -> RestaurantOut:
    return RestaurantOut(
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


def ranked_restaurants(cache: CandidateCache, session_id: str) -> list[RestaurantOut]:
    candidates = cache.get(session_id)
    if candidates is None:
        raise ResultsNotFound(session_id)
    return [_to_restaurant(c) for c in rank_candidates(candidates)]
