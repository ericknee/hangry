"""Thin async client for the Google Places API (New).

Uses field masks deliberately: Essentials-tier fields for bulk search so
early candidate retrieval stays free, and Pro/Enterprise fields (ratings,
reviews, photos) only when building the final shortlist. See the project
doc's "APIs & feasibility" section for the tier breakdown.
"""

from __future__ import annotations

import os

import httpx

PLACES_BASE_URL = "https://places.googleapis.com/v1"

# Essentials tier — safe to request on every bulk search call.
SEARCH_FIELD_MASK = "places.id,places.displayName,places.formattedAddress,places.location"

# Pro/Enterprise tier — request only for the handful of shortlist finalists.
DETAIL_FIELD_MASK = "id,displayName,formattedAddress,rating,priceLevel,userRatingCount,photos"

# Essentials tier — just enough to resolve a chosen city to coordinates.
LOCATION_FIELD_MASK = "id,displayName,formattedAddress,location"


class PlacesClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ["GOOGLE_PLACES_API_KEY"]

    async def search_text(
        self, query: str, *, lat: float, lng: float, radius_m: int = 5000
    ) -> list[dict]:
        """Bulk text search, Essentials fields only."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{PLACES_BASE_URL}/places:searchText",
                headers={
                    "X-Goog-Api-Key": self.api_key,
                    "X-Goog-FieldMask": SEARCH_FIELD_MASK,
                },
                json={
                    "textQuery": query,
                    "locationBias": {
                        "circle": {
                            "center": {"latitude": lat, "longitude": lng},
                            "radius": radius_m,
                        }
                    },
                },
            )
            resp.raise_for_status()
            return resp.json().get("places", [])

    async def autocomplete_cities(self, input_text: str) -> list[dict]:
        """City-only autocomplete predictions, Essentials tier (Autocomplete (New))."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{PLACES_BASE_URL}/places:autocomplete",
                headers={"X-Goog-Api-Key": self.api_key},
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
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{PLACES_BASE_URL}/places/{place_id}",
                headers={
                    "X-Goog-Api-Key": self.api_key,
                    "X-Goog-FieldMask": LOCATION_FIELD_MASK,
                },
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
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{PLACES_BASE_URL}/places/{place_id}",
                headers={
                    "X-Goog-Api-Key": self.api_key,
                    "X-Goog-FieldMask": DETAIL_FIELD_MASK,
                },
            )
            resp.raise_for_status()
            return resp.json()
