import httpx
from api.core.candidate_cache import CandidateCache, get_candidate_cache
from api.core.places import get_places
from api.db.database import get_db
from api.db.models import SessionRecord
from api.main import app
from fastapi.testclient import TestClient

SETUP = {"after": "dinner", "price_levels": [2], "dietary": "vegan", "mode": "walk", "minutes": 10}
PLACE = {
    "id": "p1",
    "displayName": {"text": "Green Bowl"},
    "formattedAddress": "1 Main St",
    "location": {"latitude": 37.775, "longitude": -122.419},
    "rating": 4.6,
    "userRatingCount": 300,
}


class FakeDb:
    def __init__(self, record: SessionRecord | None) -> None:
        self.record = record
        self.commits = 0

    async def get(self, model, key):
        return self.record

    async def commit(self) -> None:
        self.commits += 1


class FakePlaces:
    def __init__(self, response: list[dict] | Exception) -> None:
        self.response = response
        self.calls: list[dict] = []

    async def search_text(self, query: str, **kwargs):
        self.calls.append({"query": query, **kwargs})
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


HERE = {"lat": 37.775, "lng": -122.419}


def record(location: dict | None = HERE, query: str = "") -> SessionRecord:
    return SessionRecord(id="s1", mode="solo", state={"initial_query": query, "location": location})


def post(db: FakeDb, places: FakePlaces, cache: CandidateCache, body: dict = SETUP):
    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_places] = lambda: places
    app.dependency_overrides[get_candidate_cache] = lambda: cache
    try:
        return TestClient(app).post("/sessions/s1/search", json=body)
    finally:
        app.dependency_overrides.clear()


def test_search_caches_candidates_and_records_setup():
    rec, cache = record(query="noodles"), CandidateCache()
    db, places = FakeDb(rec), FakePlaces([PLACE] * 5)
    resp = post(db, places, cache)

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
    resp = post(FakeDb(None), FakePlaces([]), CandidateCache())
    assert resp.status_code == 404


def test_session_without_location_is_400():
    resp = post(FakeDb(record(location=None)), FakePlaces([]), CandidateCache())
    assert resp.status_code == 400


def test_places_failure_is_502_and_nothing_is_cached_or_recorded():
    rec, cache = record(), CandidateCache()
    db = FakeDb(rec)
    resp = post(db, FakePlaces(httpx.ConnectError("down")), cache)
    assert resp.status_code == 502
    assert cache.get("s1") is None
    assert "setup" not in rec.state
    assert db.commits == 0


def test_invalid_setup_is_rejected():
    resp = post(FakeDb(record()), FakePlaces([]), CandidateCache(), {**SETUP, "minutes": 3})
    assert resp.status_code == 422


def get_results(cache: CandidateCache):
    app.dependency_overrides[get_candidate_cache] = lambda: cache
    try:
        return TestClient(app).get("/sessions/s1/results")
    finally:
        app.dependency_overrides.clear()


def test_results_are_ranked_and_expose_user_facing_fields():
    cache = CandidateCache()
    post(
        FakeDb(record()),
        FakePlaces(
            [
                {**PLACE, "id": "few", "rating": 5.0, "userRatingCount": 3},
                {**PLACE, "id": "many", "rating": 4.6, "userRatingCount": 800},
                # Lower-rated filler keeps the pool average below 4.6.
                {**PLACE, "id": "bare", "rating": 3.8, "primaryType": "thai_restaurant"},
                {**PLACE, "id": "x1", "rating": 3.8},
                {**PLACE, "id": "x2", "rating": 3.8},
            ]
        ),
        cache,
    )
    resp = get_results(cache)
    assert resp.status_code == 200
    restaurants = resp.json()["restaurants"]
    assert [r["place_id"] for r in restaurants][0] == "many"
    assert set(restaurants[0]) == {
        "place_id",
        "name",
        "address",
        "cuisine",
        "rating",
        "rating_count",
        "price_level",
        "distance_m",
        "maps_uri",
    }


def test_results_missing_or_expired_is_404():
    assert get_results(CandidateCache()).status_code == 404


def test_cache_entries_expire():
    now = [0.0]
    cache = CandidateCache(ttl_seconds=10, clock=lambda: now[0])
    cache.set("s1", [])
    assert cache.get("s1") == []
    now[0] = 11.0
    assert cache.get("s1") is None
