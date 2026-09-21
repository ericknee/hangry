"""Borda-count aggregation: each member ranks candidates; points awarded by
rank position are summed across members.

Less sensitive to score-magnitude skew than average-utility (a member who
rates everything a 9 or a 2 doesn't warp the outcome) since only relative
ORDER within each member's scores is used.
"""

from __future__ import annotations

from agent.state import Candidate


def score_all(candidates: list[Candidate]) -> dict[str, float]:
    """Return {place_id: borda_points} across the full candidate set."""
    if not candidates:
        return {}

    member_ids = candidates[0]["member_scores"].keys()
    n = len(candidates)
    points: dict[str, float] = {c["place_id"]: 0.0 for c in candidates}

    for member_id in member_ids:
        ranked = sorted(
            candidates, key=lambda c: c["member_scores"].get(member_id, 0.0), reverse=True
        )
        for rank, candidate in enumerate(ranked):
            points[candidate["place_id"]] += n - rank - 1

    return points
