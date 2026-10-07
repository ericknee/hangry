"""Candidate retrieval: run the Places search and map results into `Candidate`s."""

from __future__ import annotations

import math

from agent.places_client import PlacesClient
from agent.types import Candidate, SearchParams

MIN_RATING = 3.5
RETRY_MIN_RATING = 3.0
THIN_RESULTS = 5  # fewer candidates than this triggers one retry at the lower rating floor

_PRICE_LEVELS = {
    "PRICE_LEVEL_INEXPENSIVE": 1,
    "PRICE_LEVEL_MODERATE": 2,
    "PRICE_LEVEL_EXPENSIVE": 3,
    "PRICE_LEVEL_VERY_EXPENSIVE": 4,
}


def _distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine distance in metres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(a))


def _to_candidates(places: list[dict], lat: float, lng: float) -> list[Candidate]:
    candidates: list[Candidate] = []
    for p in places:
        if p.get("businessStatus", "OPERATIONAL") != "OPERATIONAL":
            continue  # permanently or temporarily closed
        loc = p.get("location")
        candidates.append(
            Candidate(
                place_id=p["id"],
                name=p.get("displayName", {}).get("text", ""),
                address=p.get("formattedAddress", ""),
                rating=p.get("rating"),
                price_level=_PRICE_LEVELS.get(p.get("priceLevel", "")),
                cuisine=p.get("primaryType"),
                distance_m=(
                    _distance_m(lat, lng, loc["latitude"], loc["longitude"]) if loc else None
                ),
                rating_count=p.get("userRatingCount"),
                maps_uri=p.get("googleMapsUri"),
                aggregate_score=None,
            )
        )
    return candidates


async def retrieve_candidates(
    places: PlacesClient, *, lat: float, lng: float, params: SearchParams
) -> list[Candidate]:
    """Open-now search at a 3.5 rating floor; one retry at 3.0 if the result is thin."""

    async def search(min_rating: float) -> list[Candidate]:
        found = await places.search_text(
            params.query,
            lat=lat,
            lng=lng,
            radius_m=params.radius_m,
            included_type=params.included_type,
            price_levels=params.price_levels,
            min_rating=min_rating,
            open_now=True,
        )
        return _to_candidates(found, lat, lng)

    candidates = await search(MIN_RATING)
    if len(candidates) < THIN_RESULTS:
        candidates = await search(RETRY_MIN_RATING)
    return candidates
