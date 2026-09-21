"""Aggregate & retrieve node.

Fans in every member's preferences, retrieves/re-scores candidates against
each member, then combines per-member scores into one aggregate score per
candidate using the winning strategy from the evaluation plan (default:
maximin, pending the synthetic-scenario results — see aggregation/__init__.py).
"""

from __future__ import annotations

from agent.aggregation import maximin
from agent.state import Candidate, TableTalkState

DEFAULT_STRATEGY = maximin.score


async def aggregate_and_retrieve(state: TableTalkState) -> TableTalkState:
    # TODO: real Places retrieval + per-member re-ranking goes here.
    candidates: list[Candidate] = state["candidates"]

    for candidate in candidates:
        candidate["aggregate_score"] = DEFAULT_STRATEGY(candidate)

    candidates.sort(key=lambda c: c["aggregate_score"] or 0.0, reverse=True)

    state["candidates"] = candidates
    state["consensus_score"] = candidates[0]["aggregate_score"] if candidates else 0.0
    return state
