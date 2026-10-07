from typing import Annotated, Literal

from pydantic import BaseModel, Field

SessionMode = Literal["solo", "group"]


class LocationInput(BaseModel):
    # Absent for "Current location", which comes from the browser rather than Places.
    place_id: str | None = None
    lat: float
    lng: float
    formatted_address: str | None = None


class CreateSessionRequest(BaseModel):
    mode: SessionMode
    initial_query: str
    location: LocationInput | None = None


class SessionResponse(BaseModel):
    session_id: str
    mode: SessionMode
    share_url: str | None


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


class ResultsResponse(BaseModel):
    """All candidates, best first. The client shows the first 3, then the rest on request."""

    restaurants: list[RestaurantOut]
