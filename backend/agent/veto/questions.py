"""Deterministic question selection — no LLM.

Questions are veto-style ("anything you'd skip?") over candidate attributes.
The next question is whichever attribute splits the *remaining* candidates
most evenly, so attributes that don't discriminate are never asked.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Callable
from typing import TypedDict

from agent.models import Candidate


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


MAX_QUESTIONS = 3
MIN_CANDIDATES = 3  # stop asking once the field is this small
MAX_OPTIONS = 4


def _cuisine(c: Candidate) -> str | None:
    return c.get("cuisine")


def _price(c: Candidate) -> str | None:
    level = c["price_level"]
    return "$" * level if level else None


def _distance(c: Candidate) -> str | None:
    d = c.get("distance_m")
    if d is None:
        return None
    if d <= 800:
        return "Walking distance"
    return "Short drive" if d <= 3000 else "Farther out"


# attribute -> (prompt, extractor)
POOL: dict[str, tuple[str, Callable[[Candidate], str | None]]] = {
    "cuisine": ("Anything you'd skip tonight?", _cuisine),
    "price": ("Any price range you'd skip?", _price),
    "distance": ("Anything too far?", _distance),
}


def _label(value: str) -> str:
    return value.removesuffix("_restaurant").replace("_", " ").title()


def _counts(candidates: list[Candidate], attribute: str) -> Counter[str]:
    extract = POOL[attribute][1]
    return Counter(v for c in candidates if (v := extract(c)) is not None)


def split_score(candidates: list[Candidate], attribute: str) -> float:
    """Normalized entropy in [0, 1] of the attribute across candidates; 0 if it can't split."""
    counts = _counts(candidates, attribute)
    total = sum(counts.values())
    if len(counts) < 2:
        return 0.0
    entropy = -sum(n / total * math.log2(n / total) for n in counts.values())
    return entropy / math.log2(len(counts))


def apply_vetoes(candidates: list[Candidate], vetoes: dict[str, list[str]]) -> list[Candidate]:
    """Drop candidates whose attribute value was vetoed; unknown values are never vetoed."""
    return [
        c
        for c in candidates
        if not any(POOL[attr][1](c) in values for attr, values in vetoes.items() if attr in POOL)
    ]


def next_question(
    candidates: list[Candidate], asked_ids: list[str], vetoes: dict[str, list[str]]
) -> Question | None:
    """Best unasked question for one member, or None when they're done."""
    remaining = apply_vetoes(candidates, vetoes)
    if len(asked_ids) >= MAX_QUESTIONS or len(remaining) <= MIN_CANDIDATES:
        return None

    scored = [(split_score(remaining, attr), attr) for attr in POOL if attr not in asked_ids]
    score, attribute = max(scored, default=(0.0, ""))
    if score == 0.0:
        return None

    top = [v for v, _ in _counts(remaining, attribute).most_common(MAX_OPTIONS)]
    options: list[QuestionOption] = [{"label": _label(v), "value": v} for v in top]
    options.append({"label": "Nothing, I'm easy", "value": None})
    return {
        "id": attribute,
        "prompt": POOL[attribute][0],
        "attribute": attribute,
        "options": options,
    }
