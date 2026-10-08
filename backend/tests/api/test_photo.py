import httpx
from agent.types import Candidate
from api.deps import get_candidate_cache, get_places
from api.main import app
from api.sessions.cache import CandidateCache
from fastapi.testclient import TestClient


def candidate(place_id: str, photo_name: str | None) -> Candidate:
    return Candidate(
        place_id=place_id,
        name="n",
        address="a",
        rating=4.0,
        price_level=None,
        photo_name=photo_name,
        aggregate_score=None,
    )


class FakePlaces:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[tuple[str, int]] = []
        self.closed = False

    async def open_photo(self, photo_name: str, *, max_width_px: int) -> httpx.Response:
        self.calls.append((photo_name, max_width_px))
        if self.error:
            raise self.error
        return httpx.Response(
            200, headers={"content-type": "image/jpeg"}, stream=httpx.ByteStream(b"JPEGBYTES")
        )


def get_photo(cache: CandidateCache, places: FakePlaces, place_id: str = "p1"):
    app.dependency_overrides[get_candidate_cache] = lambda: cache
    app.dependency_overrides[get_places] = lambda: places
    try:
        return TestClient(app).get(f"/sessions/s1/restaurants/{place_id}/photo")
    finally:
        app.dependency_overrides.clear()


def cache_with(*candidates: Candidate) -> CandidateCache:
    cache = CandidateCache()
    cache.set("s1", list(candidates))
    return cache


def test_photo_streams_bytes_with_browser_cache_header():
    places = FakePlaces()
    resp = get_photo(cache_with(candidate("p1", "places/p1/photos/abc")), places)
    assert resp.status_code == 200
    assert resp.content == b"JPEGBYTES"
    assert resp.headers["content-type"] == "image/jpeg"
    assert resp.headers["cache-control"] == "private, max-age=1800"
    assert places.calls == [("places/p1/photos/abc", 800)]


def test_photo_404_for_unknown_session_unknown_place_or_no_photo():
    places = FakePlaces()
    assert get_photo(CandidateCache(), places).status_code == 404
    assert get_photo(cache_with(candidate("other", "x")), places).status_code == 404
    assert get_photo(cache_with(candidate("p1", None)), places).status_code == 404
    assert places.calls == []  # no billed request for any of these


def test_photo_upstream_failure_is_502():
    resp = get_photo(
        cache_with(candidate("p1", "places/p1/photos/abc")),
        FakePlaces(httpx.ConnectError("boom")),
    )
    assert resp.status_code == 502
