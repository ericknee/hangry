from api.utils.group_tally import tally_votes

RANKED = ["a", "b", "c"]


def test_most_total_wins_and_names_follow_the_sign():
    tallies = tally_votes(
        [
            ("Sam", "a", 1),
            ("Sam", "b", 1),
            ("Sam", "c", -1),
            ("Alex", "a", -1),
            ("Alex", "b", 1),
            ("Alex", "c", -1),
        ],
        RANKED,
    )
    assert [t.place_id for t in tallies] == ["b", "a", "c"]
    best = tallies[0]
    assert (best.score, best.likes, best.dislikes) == (2, 2, 0)
    assert best.liked_by == ["Sam", "Alex"] and best.disliked_by == []
    assert tallies[2].disliked_by == ["Sam", "Alex"]


def test_ties_keep_the_search_ranking():
    tallies = tally_votes([("Sam", "c", 1), ("Sam", "a", 1), ("Sam", "b", 1)], RANKED)
    assert [t.place_id for t in tallies] == ["a", "b", "c"]


def test_strength_counts_in_the_score_but_not_in_the_like_count():
    [top, *_] = tally_votes([("Sam", "c", 3), ("Alex", "c", 1), ("Alex", "a", 1)], RANKED)
    assert (top.place_id, top.score, top.likes) == ("c", 4, 2)


def test_zero_votes_count_for_nothing_and_name_nobody():
    tallies = tally_votes([("Slow", p, 0) for p in RANKED] + [("Sam", "b", 1)], RANKED)
    assert tallies[0].place_id == "b"
    assert all(t.disliked_by == [] for t in tallies)
    assert tallies[0].liked_by == ["Sam"]


def test_every_place_appears_even_without_votes_and_unknown_places_are_ignored():
    tallies = tally_votes([("Sam", "zzz", 1)], RANKED)
    assert [t.place_id for t in tallies] == RANKED
    assert all(t.score == 0 for t in tallies)
