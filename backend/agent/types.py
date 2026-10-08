"""Shared type definitions for the search pipeline."""

from __future__ import annotations

from dataclasses import dataclass
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
    # First Places photo. The name expires, so it lives only as long as the candidate cache.
    photo_name: NotRequired[str | None]
    photo_author: NotRequired[str | None]
    photo_author_uri: NotRequired[str | None]
    # Final score once ranking has run.
    aggregate_score: float | None


@dataclass(frozen=True)
class SearchParams:
    """Places Text Search parameters derived from the setup answers."""

    query: str
    included_type: str | None
    price_levels: list[str]
    radius_m: int


class QuestionOption(TypedDict):
    """One tap target. `value` is None for the "don't care" option."""

    label: str
    value: str | None


class Question(TypedDict):
    """A tap-to-answer veto question, built from the remaining candidates (no LLM)."""

    id: str
    prompt: str
    # Candidate attribute this question vetoes on, e.g. "cuisine".
    attribute: str
    options: list[QuestionOption]
