"""Shared test doubles and helpers for the sessions endpoint tests."""

from api.db.database import get_db
from api.db.models import SessionRecord
from api.deps import get_candidate_cache, get_places
from api.main import app
from api.sessions.cache import CandidateCache
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
HERE = {"lat": 37.775, "lng": -122.419}


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


def record(location: dict | None = HERE, query: str = "") -> SessionRecord:
    return SessionRecord(id="s1", mode="solo", state={"initial_query": query, "location": location})


def post_search(db: FakeDb, places: FakePlaces, cache: CandidateCache, body: dict = SETUP):
    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_places] = lambda: places
    app.dependency_overrides[get_candidate_cache] = lambda: cache
    try:
        return TestClient(app).post("/sessions/s1/search", json=body)
    finally:
        app.dependency_overrides.clear()


def get_results(cache: CandidateCache):
    app.dependency_overrides[get_candidate_cache] = lambda: cache
    try:
        return TestClient(app).get("/sessions/s1/results")
    finally:
        app.dependency_overrides.clear()
