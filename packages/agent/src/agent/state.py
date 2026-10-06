"""Shared state object carried through the Hangry LangGraph graph.

Solo mode is not a different graph — it is this same graph invoked with
`members` of length 1, so the aggregation node becomes a no-op pass-through
and the consensus check resolves on the first pass.
"""

from __future__ import annotations

from typing import Literal, NotRequired, TypedDict


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


class Preference(TypedDict, total=False):
    """A single answered elicitation question for one member."""

    question_id: str
    question_text: str
    selected_option: str
    # Free-form structured slot this answer fills, e.g. {"cuisine": "thai"}
    slot: dict[str, str]


class MemberState(TypedDict):
    """Per-participant elicitation state. One of these per session member."""

    member_id: str
    display_name: str
    preferences: list[Preference]
    # Attribute -> values this member won't do, e.g. {"cuisine": ["pizza"]}.
    vetoes: dict[str, list[str]]
    asked_question_ids: list[str]
    # Set True once this member's branch has nothing more useful to ask.
    elicitation_done: bool
    # Most limiting / hardest-to-satisfy constraint, used to target follow-ups.
    blocking_constraint: str | None


class Candidate(TypedDict):
    """A scored restaurant candidate, post-retrieval and post-ranking."""

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
    # Per-member fit score in [0, 1], keyed by member_id.
    member_scores: dict[str, float]
    # Final aggregated score once the aggregation node has run.
    aggregate_score: float | None
    reason: str | None


class HangryState(TypedDict):
    """The full graph state. Solo mode sets `members` to length 1."""

    session_id: str
    mode: Literal["solo", "group"]
    members: list[MemberState]
    candidates: list[Candidate]
    consensus_score: float | None
    consensus_threshold: float
    round_count: int
    max_rounds: int
    shortlist: list[Candidate]
    explanation: str | None
