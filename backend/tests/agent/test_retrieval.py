import pytest
from agent.search.params import build_search_params
from agent.search.retrieval import MIN_RATING, RETRY_MIN_RATING, retrieve_candidates


def params(**overrides):
    base = dict(
        after="dinner", dietary="none", craving="", price_levels=[], mode="drive", minutes=20
    )
    return build_search_params(**{**base, **overrides})


def place(i: int, **extra) -> dict:
    return {
        "id": f"p{i}",
        "displayName": {"text": f"Place {i}"},
        "formattedAddress": "addr",
        "location": {"latitude": 37.0, "longitude": -122.0},
        "primaryType": "thai_restaurant",
        "rating": 4.5,
        "userRatingCount": 120,
        "priceLevel": "PRICE_LEVEL_MODERATE",
        "googleMapsUri": "https://maps.example/p",
        **extra,
    }


class FakePlaces:
    def __init__(self, *responses: list[dict]) -> None:
        self.responses = list(responses)
        self.calls: list[dict] = []

    async def search_text(self, query: str, **kwargs) -> list[dict]:
        self.calls.append({"query": query, **kwargs})
        return self.responses.pop(0)


async def test_no_retry_when_enough_results():
    fake = FakePlaces([place(i) for i in range(5)])
    result = await retrieve_candidates(fake, lat=37.0, lng=-122.0, params=params())
    assert len(result) == 5
    assert len(fake.calls) == 1
    assert fake.calls[0]["min_rating"] == MIN_RATING
    assert fake.calls[0]["open_now"] is True


async def test_retries_at_lower_rating_when_thin():
    fake = FakePlaces([place(1)], [place(i) for i in range(6)])
    result = await retrieve_candidates(fake, lat=37.0, lng=-122.0, params=params())
    assert len(result) == 6
    assert [c["min_rating"] for c in fake.calls] == [MIN_RATING, RETRY_MIN_RATING]


async def test_closed_places_dropped_and_fields_mapped():
    # Five open places (so no retry) plus one permanently closed.
    fake = FakePlaces(
        [place(1), place(2, businessStatus="CLOSED_PERMANENTLY")]
        + [place(i, businessStatus="OPERATIONAL") for i in range(3, 7)]
    )
    result = await retrieve_candidates(fake, lat=37.0, lng=-122.0, params=params())
    assert [c["place_id"] for c in result] == ["p1", "p3", "p4", "p5", "p6"]
    c = result[0]
    assert (c["name"], c["rating"], c["price_level"], c["cuisine"]) == (
        "Place 1",
        4.5,
        2,
        "thai_restaurant",
    )
    assert c["rating_count"] == 120
    assert c["distance_m"] == pytest.approx(0, abs=1)


async def test_first_photo_and_author_mapped_and_absent_photo_is_none():
    photo = {
        "name": "places/p1/photos/abc",
        "authorAttributions": [{"displayName": "Ann", "uri": "https://maps.example/ann"}],
    }
    fake = FakePlaces(
        [place(1, photos=[photo, {"name": "places/p1/photos/def"}])]
        + [place(i) for i in range(2, 7)]
    )
    result = await retrieve_candidates(fake, lat=37.0, lng=-122.0, params=params())
    assert result[0]["photo_name"] == "places/p1/photos/abc"
    assert result[0]["photo_author"] == "Ann"
    assert result[0]["photo_author_uri"] == "https://maps.example/ann"
    assert result[1]["photo_name"] is None
