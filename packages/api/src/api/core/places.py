from agent.clients.places import PlacesClient
from fastapi import Request


def get_places(request: Request) -> PlacesClient:
    """The app-wide PlacesClient created in `main.lifespan`."""
    return request.app.state.places
