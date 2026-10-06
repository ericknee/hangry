"""Shared data shapes for the search pipeline (retrieval, ranking, question selection)."""

from __future__ import annotations

from typing import NotRequired, TypedDict


class QuestionOption(TypedDict):
    """One tap target. `value` is None for the "don't care" option."""

    label: str
    value: str | None


class Question(TypedDict):
    """A tap-to-answer question, built from the remaining candidates (no LLM)."""

    id: str
    prompt: str
    # Candidate attribute this question vetoes on, e.g. "cuisine".
    attribute: str
    options: list[QuestionOption]


class Candidate(TypedDict):
    """A restaurant candidate, post-retrieval and post-ranking."""

    place_id: str
    name: str
    address: str
    rating: float | None
    price_level: int | None
    # Attributes the question pool splits on; absent when retrieval can't supply them.
    cuisine: NotRequired[str | None]
    distance_m: NotRequired[float | None]
    rating_count: NotRequired[int | None]
    maps_uri: NotRequired[str | None]
    # Final score once ranking has run.
    aggregate_score: float | None
