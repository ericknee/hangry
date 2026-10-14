from api.deps import get_places
from api.main import app
from fastapi.testclient import TestClient

TOKEN = "3f1c0f0e-8a52-4f0a-9d56-0f2c7d1f5b11"


class FakePlaces:
    def __init__(self) -> None:
        self.tokens: list[str | None] = []

    async def autocomplete_cities(self, input_text: str, *, session_token: str | None = None):
        self.tokens.append(session_token)
        return [{"place_id": "c1", "description": "Santa Barbara, CA, USA"}]

    async def get_place_location(self, place_id: str, *, session_token: str | None = None):
        self.tokens.append(session_token)
        return {"place_id": place_id, "lat": 34.42, "lng": -119.7, "formatted_address": "SB"}


def get(path: str, places: FakePlaces):
    app.dependency_overrides[get_places] = lambda: places
    try:
        return TestClient(app).get(path)
    finally:
        app.dependency_overrides.clear()


def test_autocomplete_forwards_the_session_token():
    places = FakePlaces()
    resp = get(f"/places/autocomplete?input=sant&session_token={TOKEN}", places)
    assert resp.status_code == 200
    assert places.tokens == [TOKEN]


def test_city_location_forwards_the_session_token():
    places = FakePlaces()
    resp = get(f"/places/cities/c1?session_token={TOKEN}", places)
    assert resp.status_code == 200
    assert places.tokens == [TOKEN]


def test_session_token_is_optional():
    places = FakePlaces()
    assert get("/places/autocomplete?input=sant", places).status_code == 200
    assert get("/places/cities/c1", places).status_code == 200
    assert places.tokens == [None, None]


def test_malformed_session_token_is_rejected():
    places = FakePlaces()
    assert get("/places/autocomplete?input=sant&session_token=nope", places).status_code == 422
    assert get("/places/cities/c1?session_token=nope", places).status_code == 422
    assert places.tokens == []
