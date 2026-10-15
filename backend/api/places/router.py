from typing import Annotated
from uuid import UUID

import httpx
from agent.places_client import PlacesClient
from fastapi import APIRouter, Depends, HTTPException, Path, Query

from api.deps import get_places
from api.errors import PLACES_ERRORS, describe_error
from api.places.types import CityLocation, CityPrediction, PlaceId
from api.ratelimit import rate_limit

router = APIRouter(prefix="/places", tags=["places"])


@router.get(
    "/autocomplete",
    response_model=list[CityPrediction],
    dependencies=[Depends(rate_limit("autocomplete", "rate_limit_autocomplete_ip_per_min"))],
)
async def autocomplete(
    input: Annotated[str, Query(min_length=1, max_length=100)],
    places: Annotated[PlacesClient, Depends(get_places)],
    session_token: Annotated[UUID, Query()],
) -> list[CityPrediction]:
    try:
        predictions = await places.autocomplete_cities(input, session_token=str(session_token))
    except PLACES_ERRORS as exc:
        raise HTTPException(
            status_code=502, detail=f"Places autocomplete failed: {describe_error(exc)}"
        ) from exc
    return [CityPrediction(**p) for p in predictions]


@router.get(
    "/cities/{place_id}",
    response_model=CityLocation,
    dependencies=[Depends(rate_limit("city_lookup", "rate_limit_city_lookup_ip_per_min"))],
)
async def city_location(
    place_id: Annotated[PlaceId, Path()],
    places: Annotated[PlacesClient, Depends(get_places)],
    session_token: Annotated[UUID, Query()],
) -> CityLocation:
    try:
        location = await places.get_place_location(place_id, session_token=str(session_token))
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (400, 404):
            raise HTTPException(status_code=404, detail="Unknown place id") from exc
        raise HTTPException(
            status_code=502, detail=f"Places lookup failed: {describe_error(exc)}"
        ) from exc
    except PLACES_ERRORS as exc:
        raise HTTPException(
            status_code=502, detail=f"Places lookup failed: {describe_error(exc)}"
        ) from exc
    return CityLocation(**location)
