from agent.models import Candidate
from agent.veto.questions import MAX_QUESTIONS, apply_vetoes, next_question, split_score


def cand(i: int, cuisine: str | None, price: int | None = 2, dist: float | None = 500) -> Candidate:
    return {
        "place_id": str(i),
        "name": f"p{i}",
        "address": "",
        "rating": None,
        "price_level": price,
        "cuisine": cuisine,
        "distance_m": dist,
        "aggregate_score": None,
    }


MIXED = [cand(i, c) for i, c in enumerate(["thai", "pizza", "thai", "sushi", "pizza", "thai"])]


def test_split_score_zero_when_uniform():
    assert split_score([cand(i, "thai") for i in range(5)], "cuisine") == 0.0


def test_split_score_higher_when_even():
    even = [cand(i, c) for i, c in enumerate(["a", "b", "a", "b"])]
    skewed = [cand(i, c) for i, c in enumerate(["a", "a", "a", "b"])]
    assert split_score(even, "cuisine") > split_score(skewed, "cuisine")


def test_asks_most_discriminating_attribute_and_skips_uniform_ones():
    q = next_question(MIXED, [], {})
    assert q is not None
    assert q["attribute"] == "cuisine"  # price and distance are uniform here
    assert q["options"][-1]["value"] is None  # "don't care" always offered


def test_stops_when_few_candidates_or_max_questions():
    assert next_question(MIXED[:3], [], {}) is None
    assert next_question(MIXED, ["a"] * MAX_QUESTIONS, {}) is None


def test_does_not_repeat_asked_question():
    assert next_question(MIXED, ["cuisine"], {}) is None  # nothing else splits


def test_vetoes_filter_and_ignore_unknown_values():
    kept = apply_vetoes(MIXED + [cand(9, None)], {"cuisine": ["pizza"]})
    assert [c["cuisine"] for c in kept].count("pizza") == 0
    assert any(c["cuisine"] is None for c in kept)
