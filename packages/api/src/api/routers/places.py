from typing import Annotated

import httpx
from agent.clients.places import PlacesClient
from fastapi import APIRouter, Depends, HTTPException, Query

from api.core.places import get_places
from api.schemas.places import CityLocation, CityPrediction

router = APIRouter(prefix="/places", tags=["places"])


@router.get("/autocomplete", response_model=list[CityPrediction])
async def autocomplete(
    input: Annotated[str, Query(min_length=1)],
    places: Annotated[PlacesClient, Depends(get_places)],
) -> list[CityPrediction]:
    try:
        predictions = await places.autocomplete_cities(input)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Places autocomplete failed") from exc
    return [CityPrediction(**p) for p in predictions]


@router.get("/cities/{place_id}", response_model=CityLocation)
async def city_location(
    place_id: str,
    places: Annotated[PlacesClient, Depends(get_places)],
) -> CityLocation:
    try:
        location = await places.get_place_location(place_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (400, 404):
            raise HTTPException(status_code=404, detail="Unknown place id") from exc
        raise HTTPException(status_code=502, detail="Places lookup failed") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Places lookup failed") from exc
    return CityLocation(**location)
