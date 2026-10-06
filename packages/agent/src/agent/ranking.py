"""Rank candidates by review-adjusted rating."""

from __future__ import annotations

from agent.state import Candidate

# Bayesian average: a place needs about this many reviews before its own rating
# counts as much as the average rating of all results.
PRIOR_WEIGHT = 50


def rank_candidates(candidates: list[Candidate]) -> list[Candidate]:
    """Best first. Unrated places go last; ties break on distance. Sets `aggregate_score`."""
    rated = [c["rating"] for c in candidates if c["rating"] is not None]
    mean = sum(rated) / len(rated) if rated else 0.0

    def scored(c: Candidate) -> Candidate:
        if c["rating"] is None:
            return {**c, "aggregate_score": None}
        votes = c.get("rating_count") or 0
        score = (votes * c["rating"] + PRIOR_WEIGHT * mean) / (votes + PRIOR_WEIGHT)
        return {**c, "aggregate_score": score}

    def sort_key(c: Candidate) -> tuple[int, float, float]:
        distance = c.get("distance_m")
        score = c["aggregate_score"]
        return (
            0 if score is not None else 1,
            -(score or 0.0),
            distance if distance is not None else float("inf"),
        )

    return sorted((scored(c) for c in candidates), key=sort_key)
