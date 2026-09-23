from agent.clients.places import PlacesClient
from fastapi import APIRouter, HTTPException, Query

from api.schemas.places import CityLocation, CityPrediction

router = APIRouter(prefix="/places", tags=["places"])


def _client() -> PlacesClient:
    try:
        return PlacesClient()
    except KeyError as exc:
        raise HTTPException(status_code=503, detail="Google Places API is not configured") from exc


@router.get("/autocomplete", response_model=list[CityPrediction])
async def autocomplete(input: str = Query(min_length=1)) -> list[CityPrediction]:
    predictions = await _client().autocomplete_cities(input)
    return [CityPrediction(**p) for p in predictions]


@router.get("/cities/{place_id}", response_model=CityLocation)
async def city_location(place_id: str) -> CityLocation:
    location = await _client().get_place_location(place_id)
    return CityLocation(**location)
