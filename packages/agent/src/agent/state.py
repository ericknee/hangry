"""Shared state object carried through the TableTalk LangGraph graph.

Solo mode is not a different graph — it is this same graph invoked with
`members` of length 1, so the aggregation node becomes a no-op pass-through
and the consensus check resolves on the first pass.
"""

from __future__ import annotations

from typing import Literal, TypedDict


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
    # Per-member fit score in [0, 1], keyed by member_id.
    member_scores: dict[str, float]
    # Final aggregated score once the aggregation node has run.
    aggregate_score: float | None
    reason: str | None


class TableTalkState(TypedDict):
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
