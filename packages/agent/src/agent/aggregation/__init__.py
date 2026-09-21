"""Aggregation strategies compared in the evaluation plan.

Which strategy ships as default is decided by the synthetic fairness-scenario
evaluation (see project doc, "Evaluation plan"), not fixed here.
"""

from agent.aggregation import average_utility, borda, maximin

STRATEGIES = {
    "average_utility": average_utility.score,
    "maximin": maximin.score,
    # Borda is scored across the whole candidate set at once, not per-candidate,
    # so it's wired up directly in nodes/aggregate.py rather than through this map.
}

__all__ = ["STRATEGIES", "average_utility", "maximin", "borda"]
