from agent.places_client import PlacesClient
from fastapi import Request

from api.sessions.cache import CandidateCache


def get_places(request: Request) -> PlacesClient:
    """The app-wide PlacesClient created in `main.lifespan`."""
    return request.app.state.places


def get_candidate_cache(request: Request) -> CandidateCache:
    """The app-wide candidate cache created in `main.lifespan`."""
    return request.app.state.candidates
