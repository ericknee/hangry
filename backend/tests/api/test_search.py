import httpx
from api.sessions.cache import CandidateCache
from fakes import PLACE, SETUP, FakeDb, FakePlaces, post_search, record


def test_search_caches_candidates_and_records_setup():
    rec, cache = record(query="noodles"), CandidateCache()
    db, places = FakeDb(rec), FakePlaces([PLACE] * 5)
    resp = post_search(db, places, cache)

    assert resp.status_code == 200
    assert resp.json() == {"count": 5}
    assert [c["place_id"] for c in cache.get("s1")] == ["p1"] * 5
    assert rec.state["setup"] == SETUP
    assert rec.state["initial_query"] == "noodles"  # existing keys preserved
    assert db.commits == 1
    [call] = places.calls
    assert call["query"] == "noodles"  # the craving wins; dietary took the type filter
    assert call["included_type"] == "vegan_restaurant"
    assert call["price_levels"] == ["PRICE_LEVEL_MODERATE"]
    assert call["radius_m"] == 615  # 10 min walk
    assert (call["min_rating"], call["open_now"]) == (3.5, True)


def test_unknown_session_is_404():
    resp = post_search(FakeDb(None), FakePlaces([]), CandidateCache())
    assert resp.status_code == 404


def test_session_without_location_is_400():
    resp = post_search(FakeDb(record(location=None)), FakePlaces([]), CandidateCache())
    assert resp.status_code == 400


def test_places_failure_is_502_and_nothing_is_cached_or_recorded():
    rec, cache = record(), CandidateCache()
    db = FakeDb(rec)
    resp = post_search(db, FakePlaces(httpx.ConnectError("down")), cache)
    assert resp.status_code == 502
    assert cache.get("s1") is None
    assert "setup" not in rec.state
    assert db.commits == 0


def test_invalid_setup_is_rejected():
    resp = post_search(FakeDb(record()), FakePlaces([]), CandidateCache(), {**SETUP, "minutes": 3})
    assert resp.status_code == 422
