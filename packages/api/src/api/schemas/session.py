from pydantic import BaseModel, Field


class LocationInput(BaseModel):
    place_id: str
    lat: float
    lng: float
    formatted_address: str | None = None


class CandidateOut(BaseModel):
    place_id: str
    name: str
    address: str


class CreateSessionRequest(BaseModel):
    mode: str  # "solo" | "group"
    initial_query: str
    location: LocationInput | None = None
    radius_km: float | None = Field(default=None, gt=0, le=50)


class SessionResponse(BaseModel):
    session_id: str
    mode: str
    share_url: str | None = None
    candidates: list[CandidateOut] = []
