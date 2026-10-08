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
from api.errors import PLACES_ERRORS, describe_error
from api.sessions.cache import CandidateCache
from api.sessions.types import CreateSessionRequest, PhotoOut, RestaurantOut, SearchRequest

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


class PhotoNotFound(Exception):
    """The session's results, the place, or the place's photo is not available."""


class PhotoFetchFailed(Exception):
    """Fetching the image from Google failed (network, bad key, quota, expired name)."""


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

    # A repeat call (double-tap, retry) reuses the cached results instead of a second paid search.
    cached = cache.get(session_id)
    if cached is not None:
        return len(cached)

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
    except PLACES_ERRORS as exc:
        raise SearchFailed(describe_error(exc)) from exc

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
        photo=(
            PhotoOut(author_name=c.get("photo_author"), author_uri=c.get("photo_author_uri"))
            if c.get("photo_name")
            else None
        ),
    )


def ranked_restaurants(cache: CandidateCache, session_id: str) -> list[RestaurantOut]:
    candidates = cache.get(session_id)
    if candidates is None:
        raise ResultsNotFound(session_id)
    return [_to_restaurant(c) for c in rank_candidates(candidates)]


PHOTO_MAX_WIDTH_PX = 800  # sharp on a phone-width card at 2x density


async def open_photo(
    places: PlacesClient, cache: CandidateCache, session_id: str, place_id: str
) -> httpx.Response:
    """Open the cached candidate's photo as a streamed upstream response (caller closes it)."""
    candidates = cache.get(session_id)
    candidate = next((c for c in candidates or [] if c["place_id"] == place_id), None)
    photo_name = candidate.get("photo_name") if candidate else None
    if not photo_name:
        raise PhotoNotFound(place_id)
    try:
        return await places.open_photo(photo_name, max_width_px=PHOTO_MAX_WIDTH_PX)
    except PLACES_ERRORS as exc:
        raise PhotoFetchFailed(describe_error(exc)) from exc
