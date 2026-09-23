"""Thin async client for the Google Places API (New).

Uses field masks deliberately: Essentials-tier fields for bulk search so
early candidate retrieval stays free, and Pro/Enterprise fields (ratings,
reviews, photos) only when building the final shortlist. See the project
doc's "APIs & feasibility" section for the tier breakdown.
"""

from __future__ import annotations

import math

import httpx

PLACES_BASE_URL = "https://places.googleapis.com/v1"

# Essentials tier — safe to request on every bulk search call.
SEARCH_FIELD_MASK = "places.id,places.displayName,places.formattedAddress,places.location"

# Pro/Enterprise tier — request only for the handful of shortlist finalists.
DETAIL_FIELD_MASK = "id,displayName,formattedAddress,rating,priceLevel,userRatingCount,photos"

# Essentials tier — just enough to resolve a chosen city to coordinates.
LOCATION_FIELD_MASK = "id,displayName,formattedAddress,location"

METERS_PER_DEG_LAT = 111_320


def _bounding_box(lat: float, lng: float, radius_m: int) -> dict:
    """Rectangle enclosing a radius_m circle — Text Search only restricts by rectangle."""
    dlat = radius_m / METERS_PER_DEG_LAT
    dlng = radius_m / (METERS_PER_DEG_LAT * math.cos(math.radians(lat)))
    return {
        "rectangle": {
            "low": {"latitude": lat - dlat, "longitude": lng - dlng},
            "high": {"latitude": lat + dlat, "longitude": lng + dlng},
        }
    }


class PlacesClient:
    """Holds one pooled HTTP connection for the app's lifetime; call `aclose()` on shutdown."""

    def __init__(self, api_key: str) -> None:
        self._http = httpx.AsyncClient(
            base_url=PLACES_BASE_URL,
            headers={"X-Goog-Api-Key": api_key},
            timeout=10.0,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> PlacesClient:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    async def search_text(
        self, query: str, *, lat: float, lng: float, radius_m: int = 5000
    ) -> list[dict]:
        """Bulk text search restricted to the radius's bounding box, Essentials fields only."""
        resp = await self._http.post(
            "/places:searchText",
            headers={"X-Goog-FieldMask": SEARCH_FIELD_MASK},
            json={
                "textQuery": query,
                "locationRestriction": _bounding_box(lat, lng, radius_m),
            },
        )
        resp.raise_for_status()
        return resp.json().get("places", [])

    async def autocomplete_cities(self, input_text: str) -> list[dict]:
        """City-only autocomplete predictions, Essentials tier (Autocomplete (New))."""
        resp = await self._http.post(
            "/places:autocomplete",
            json={"input": input_text, "includedPrimaryTypes": ["locality"]},
        )
        resp.raise_for_status()
        suggestions = resp.json().get("suggestions", [])
        return [
            {
                "place_id": s["placePrediction"]["placeId"],
                "description": s["placePrediction"]["text"]["text"],
            }
            for s in suggestions
            if "placePrediction" in s
        ]

    async def get_place_location(self, place_id: str) -> dict:
        """Resolve a chosen city's place id to coordinates, Essentials fields only."""
        resp = await self._http.get(
            f"/places/{place_id}",
            headers={"X-Goog-FieldMask": LOCATION_FIELD_MASK},
        )
        resp.raise_for_status()
        data = resp.json()
        location = data["location"]
        return {
            "place_id": data["id"],
            "lat": location["latitude"],
            "lng": location["longitude"],
            "formatted_address": data.get("formattedAddress", ""),
        }

    async def get_details(self, place_id: str) -> dict:
        """Full detail fetch, Pro/Enterprise fields — call sparingly."""
        resp = await self._http.get(
            f"/places/{place_id}",
            headers={"X-Goog-FieldMask": DETAIL_FIELD_MASK},
        )
        resp.raise_for_status()
        return resp.json()
