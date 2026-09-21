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
DETAIL_FIELD_MASK = (
    "id,displayName,formattedAddress,rating,priceLevel,userRatingCount,photos"
)


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
