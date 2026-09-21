"""Maximin aggregation: score = the WORST member fit score.

Optimizes for "nobody hates this option" rather than "the average person
likes this option" — directly targets the majority-dominates-minority
failure mode average-utility is prone to.
"""

from __future__ import annotations

from agent.state import Candidate


def score(candidate: Candidate) -> float:
    scores = list(candidate["member_scores"].values())
    return min(scores) if scores else 0.0
