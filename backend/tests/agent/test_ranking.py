from agent.search.ranking import rank_candidates
from agent.types import Candidate


def cand(
    pid: str, rating: float | None, count: int | None, distance: float | None = 100
) -> Candidate:
    return {
        "place_id": pid,
        "name": pid,
        "address": "",
        "rating": rating,
        "price_level": None,
        "rating_count": count,
        "distance_m": distance,
        "aggregate_score": None,
    }


def ids(cs: list[Candidate]) -> list[str]:
    return [c["place_id"] for c in cs]


def test_many_reviews_beat_a_perfect_score_from_few():
    ranked = rank_candidates([cand("few", 5.0, 3), cand("many", 4.6, 800), cand("mid", 4.0, 100)])
    assert ids(ranked) == ["many", "few", "mid"]


def test_unrated_places_go_last():
    ranked = rank_candidates([cand("none", None, None), cand("ok", 3.6, 10)])
    assert ids(ranked) == ["ok", "none"]
    assert ranked[1]["aggregate_score"] is None
    assert ranked[0]["aggregate_score"] is not None


def test_ties_break_on_distance_and_missing_distance_is_last():
    ranked = rank_candidates(
        [cand("far", 4.5, 200, 900), cand("unknown", 4.5, 200, None), cand("near", 4.5, 200, 100)]
    )
    assert ids(ranked) == ["near", "far", "unknown"]


def test_empty_and_unrated_only():
    assert rank_candidates([]) == []
    assert ids(rank_candidates([cand("a", None, None, 50), cand("b", None, None, 10)])) == [
        "b",
        "a",
    ]
