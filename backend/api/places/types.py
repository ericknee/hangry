from typing import Annotated

from pydantic import BaseModel, StringConstraints

# Google place ids are URL-safe base64-ish. The id is interpolated into a Google URL path,
# so anything else (`/`, `?`, `..`) is rejected before it gets there.
PlaceId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,256}$")]


class CityPrediction(BaseModel):
    place_id: str
    description: str


class CityLocation(BaseModel):
    place_id: str
    lat: float
    lng: float
    formatted_address: str | None
