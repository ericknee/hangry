from api.sessions.cache import CandidateCache
from fakes import PLACE, FakeDb, FakePlaces, get_results, post_search, record


def test_results_are_ranked_and_expose_user_facing_fields():
    cache = CandidateCache()
    post_search(
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
        "photo",
    }


def test_results_missing_or_expired_is_404():
    assert get_results(CandidateCache()).status_code == 404


def test_results_expose_photo_credit_only_when_place_has_a_photo():
    cache = CandidateCache()
    photo = {
        "name": "places/p1/photos/abc",
        "authorAttributions": [{"displayName": "Ann", "uri": "https://maps.example/ann"}],
    }
    post_search(
        FakeDb(record()),
        FakePlaces(
            [{**PLACE, "id": f"p{i}"} for i in range(4)]
            + [{**PLACE, "id": "pic", "photos": [photo]}]
        ),
        cache,
    )
    by_id = {r["place_id"]: r for r in get_results(cache).json()["restaurants"]}
    assert by_id["pic"]["photo"] == {"author_name": "Ann", "author_uri": "https://maps.example/ann"}
    assert by_id["p0"]["photo"] is None
