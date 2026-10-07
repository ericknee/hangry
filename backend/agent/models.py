"""Shared data shapes for the search pipeline."""

from __future__ import annotations

from typing import NotRequired, TypedDict


class Candidate(TypedDict):
    """A restaurant candidate, post-retrieval and post-ranking."""

    place_id: str
    name: str
    address: str
    rating: float | None
    price_level: int | None
    # Attributes the veto questions split on; absent when retrieval can't supply them.
    cuisine: NotRequired[str | None]
    distance_m: NotRequired[float | None]
    rating_count: NotRequired[int | None]
    maps_uri: NotRequired[str | None]
    # Final score once ranking has run.
    aggregate_score: float | None
