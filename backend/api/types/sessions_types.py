from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

from api.types.places_types import PlaceId

SessionMode = Literal["solo", "group"]
# Stored per member and shown to the others in the session; blank means "pick one for me".
DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, max_length=30)]


class LocationInput(BaseModel):
    # Absent for "Current location", which comes from the browser rather than Places.
    place_id: PlaceId | None = None
    lat: float
    lng: float
    formatted_address: str | None = None


class CreateSessionRequest(BaseModel):
    mode: SessionMode
    # The typed craving. Stored with the session (deleted after 30 days), so it is length-limited.
    initial_query: str = Field(max_length=100)
    location: LocationInput | None = None
    # Group sessions only: the host's display name; blank or absent gets a generated one.
    name: DisplayName | None = None


class SessionResponse(BaseModel):
    session_id: str
    mode: SessionMode
    share_url: str | None
    # Group sessions only: the host's credential. The browser keeps it and sends it on later calls.
    participant_id: str | None


class SearchRequest(BaseModel):
    """The setup answers, sent in one call after the last setup page."""

    after: Literal["breakfast", "lunch", "dinner", "coffee_dessert", "drinks"]
    # 1 = "$" ... 4 = "$$$$"; empty means any price.
    price_levels: list[Annotated[int, Field(ge=1, le=4)]] = []
    dietary: Literal["none", "vegetarian", "vegan", "halal"] = "none"
    mode: Literal["walk", "drive"]
    minutes: int = Field(ge=5, le=60)


class SearchResponse(BaseModel):
    count: int


class PhotoOut(BaseModel):
    """Credit Google requires wherever the photo is shown. The image itself is served at
    `GET /sessions/{id}/restaurants/{place_id}/photo`."""

    author_name: str | None
    author_uri: str | None


class RestaurantOut(BaseModel):
    """User-facing details of one candidate; internal fields (scores, ids of members) stay out."""

    place_id: str
    name: str
    address: str
    cuisine: str | None
    rating: float | None
    rating_count: int | None
    price_level: int | None
    distance_m: float | None
    maps_uri: str | None
    # None when the place has no photo.
    photo: PhotoOut | None


class ResultsResponse(BaseModel):
    """All candidates, best first. The client shows the first 3, then the rest on request."""

    restaurants: list[RestaurantOut]
