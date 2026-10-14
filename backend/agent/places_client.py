"""Thin async client for the Google Places API (New).

Text Search is billed at the highest tier of any requested field. We use one
Enterprise-tier search per session (rating, price level) and no Atmosphere fields.
`places.photos` is Pro tier, so it does not raise the search tier; each image is a
separate billed Place Photos request. See "Places cost" in CLAUDE.md.
"""

from __future__ import annotations

import math

import httpx

PLACES_BASE_URL = "https://places.googleapis.com/v1"

# Enterprise tier (rating and priceLevel set the tier; photos is Pro) — the one search per session.
SEARCH_FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,places.location,"
    "places.primaryType,places.businessStatus,places.googleMapsUri,"
    "places.rating,places.userRatingCount,places.priceLevel,places.photos"
)

# Pro tier: `displayName` is Pro (`id` is IDs Only; `formattedAddress`, `location` are Essentials).
# This call ends an autocomplete session, and Google bills a session that ends in a Pro-or-higher
# Place Details request at the Enterprise + Atmosphere rate, whichever fields are requested.
# See "Places cost" in CLAUDE.md.
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
        # Image bytes come from Google's CDN, which must never see our API key header.
        self._media_http = httpx.AsyncClient(timeout=10.0)

    async def aclose(self) -> None:
        await self._http.aclose()
        await self._media_http.aclose()

    async def __aenter__(self) -> PlacesClient:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    async def search_text(
        self,
        query: str,
        *,
        lat: float,
        lng: float,
        radius_m: int = 5000,
        included_type: str | None = None,
        price_levels: list[str] | None = None,
        min_rating: float | None = None,
        open_now: bool = False,
    ) -> list[dict]:
        """One page (max 20) of text search results inside the radius's bounding box."""
        body: dict = {
            "textQuery": query,
            "locationRestriction": _bounding_box(lat, lng, radius_m),
            "pageSize": 20,
        }
        if included_type:
            body["includedType"] = included_type
            body["strictTypeFiltering"] = True
        if price_levels:
            body["priceLevels"] = price_levels
        if min_rating is not None:
            body["minRating"] = min_rating
        if open_now:
            body["openNow"] = True
        resp = await self._http.post(
            "/places:searchText",
            headers={"X-Goog-FieldMask": SEARCH_FIELD_MASK},
            json=body,
        )
        resp.raise_for_status()
        return resp.json().get("places", [])

    async def open_photo(self, photo_name: str, *, max_width_px: int) -> httpx.Response:
        """Open a streamed response for a photo's image bytes; the caller must close it.

        One billed Place Photos request resolves the name to a CDN `photoUri`
        (`skipHttpRedirect`), then the bytes are fetched from that URI without the key.
        """
        resp = await self._http.get(
            f"/{photo_name}/media",
            params={"maxWidthPx": max_width_px, "skipHttpRedirect": "true"},
        )
        resp.raise_for_status()
        body = resp.json()
        photo_uri = body.get("photoUri") if isinstance(body, dict) else None
        if not isinstance(photo_uri, str) or not photo_uri:
            raise ValueError("Place Photos response had no photoUri")  # mapped to 502
        request = self._media_http.build_request("GET", photo_uri)
        upstream = await self._media_http.send(request, stream=True)
        try:
            upstream.raise_for_status()
        except httpx.HTTPError:
            await upstream.aclose()
            raise
        content_type = upstream.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            await upstream.aclose()
            raise ValueError(
                f"Photo CDN returned {content_type or 'no content type'}, not an image"
            )
        return upstream

    async def autocomplete_cities(
        self, input_text: str, *, session_token: str | None = None
    ) -> list[dict]:
        """City-only autocomplete predictions, Essentials tier (Autocomplete (New)).

        `session_token` groups the typing and the closing `get_place_location` call into one billed
        session; without it every request is billed on its own.
        """
        body: dict = {"input": input_text, "includedPrimaryTypes": ["locality"]}
        if session_token:
            body["sessionToken"] = session_token
        resp = await self._http.post("/places:autocomplete", json=body)
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

    async def get_place_location(self, place_id: str, *, session_token: str | None = None) -> dict:
        """Resolve a chosen city's place id to coordinates (Pro tier, see LOCATION_FIELD_MASK).

        Pass the autocomplete session's token to end that session with this call.
        """
        resp = await self._http.get(
            f"/places/{place_id}",
            headers={"X-Goog-FieldMask": LOCATION_FIELD_MASK},
            params={"sessionToken": session_token} if session_token else None,
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
