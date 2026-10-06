import pytest
from agent.retrieval import MIN_RATING, RETRY_MIN_RATING, retrieve_candidates
from agent.search_params import build_search_params, radius_m


def params(**overrides):
    base = dict(
        after="dinner", dietary="none", craving="", price_levels=[], mode="drive", minutes=20
    )
    return build_search_params(**{**base, **overrides})


def test_radius_minutes_to_metres():
    assert radius_m("walk", 5) == 308  # 5 * 80 / 1.3
    assert radius_m("drive", 20) == 7692  # 20 * 500 / 1.3


def test_default_query_and_type_per_meal():
    assert (params(after="breakfast").query, params(after="breakfast").included_type) == (
        "breakfast",
        "breakfast_restaurant",
    )
    p = params(after="coffee_dessert")
    assert (p.query, p.included_type) == ("coffee dessert", None)
    assert params(after="drinks").included_type == "bar"


def test_craving_replaces_default_query():
    assert params(craving="  spicy ramen ").query == "spicy ramen"


def test_dietary_takes_the_type_and_its_default_query():
    p = params(after="breakfast", dietary="vegan")
    assert (p.included_type, p.query) == ("vegan_restaurant", "vegan restaurants")
    assert params(dietary="halal").query == "halal restaurants"


def test_craving_still_wins_the_query_when_dietary_applies():
    p = params(after="lunch", dietary="halal", craving="kebab")
    assert (p.included_type, p.query) == ("halal_restaurant", "kebab")


def test_price_levels_mapped_and_sorted():
    assert params(price_levels=[3, 1, 3]).price_levels == [
        "PRICE_LEVEL_INEXPENSIVE",
        "PRICE_LEVEL_EXPENSIVE",
    ]


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
