"""Average-utility aggregation: score = mean of each member's fit score.

Simplest baseline. Weak spot it's evaluated against: a majority can drag the
winner toward their preference even when it's a poor fit for one member —
see maximin.py for the strategy that guards against that.
"""

from __future__ import annotations

from agent.state import Candidate


def score(candidate: Candidate) -> float:
    scores = list(candidate["member_scores"].values())
    return sum(scores) / len(scores) if scores else 0.0
