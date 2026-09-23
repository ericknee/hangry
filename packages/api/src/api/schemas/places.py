from pydantic import BaseModel


class CityPrediction(BaseModel):
    place_id: str
    description: str


class CityLocation(BaseModel):
    place_id: str
    lat: float
    lng: float
    formatted_address: str | None = None
