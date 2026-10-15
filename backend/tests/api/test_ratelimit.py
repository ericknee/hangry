from api.config import Settings
from api.deps import get_places
from api.main import create_app
from api.ratelimit import RateLimiter
from fastapi.testclient import TestClient

TOKEN = "3f1c0f0e-8a52-4f0a-9d56-0f2c7d1f5b11"


def build(**limits: int) -> TestClient:
    settings = Settings(database_url="x", google_places_api_key="x", **limits)
    return TestClient(create_app(settings))


def test_limiter_blocks_after_limit_and_recovers_when_window_passes():
    now = [0.0]
    limiter = RateLimiter(clock=lambda: now[0])
    assert limiter.hit("k", 2, 60) is None
    assert limiter.hit("k", 2, 60) is None
    assert limiter.hit("k", 2, 60) == 60
    now[0] = 61
    assert limiter.hit("k", 2, 60) is None


def test_limit_of_zero_is_off():
    limiter = RateLimiter()
    assert all(limiter.hit("k", 0, 60) is None for _ in range(100))


def test_limiter_drops_oldest_key_when_full_of_live_keys():
    limiter = RateLimiter(clock=lambda: 0.0, max_keys=2)
    for key in ("a", "b", "c"):
        limiter.hit(key, 1, 60)
    assert limiter.hit("a", 1, 60) is None  # "a" was evicted, so it starts fresh
    assert limiter.hit("c", 1, 60) is not None


def test_requests_over_the_ip_limit_get_429_with_retry_after():
    client = build(rate_limit_places_ip_per_min=3)
    url = f"/api/places/autocomplete?input=sa&session_token={TOKEN}"
    # Validation passes but there is no Places client in this app (lifespan not run), so the
    # handler errors with 500; what matters is that the 4th request never reaches it.
    client = TestClient(client.app, raise_server_exceptions=False)
    statuses = [client.get(url).status_code for _ in range(4)]
    assert statuses[:3] != [429] * 3 and 429 not in statuses[:3]
    assert statuses[3] == 429
    assert int(client.get(url).headers["retry-after"]) >= 1


def test_per_session_limit_applies_across_ips_and_is_independent_per_session():
    client = TestClient(
        build(rate_limit_photo_ip_per_min=0, rate_limit_photo_session=2).app,
        raise_server_exceptions=False,
    )

    def photo(session: str) -> int:
        return client.get(f"/api/sessions/{session}/restaurants/p1/photo").status_code

    assert 429 not in (photo("s1"), photo("s1"))
    assert photo("s1") == 429
    assert photo("s2") != 429


def test_limits_come_from_environment(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PHOTO_IP_PER_MIN", "7")
    assert Settings(database_url="x", google_places_api_key="x").rate_limit_photo_ip_per_min == 7


def test_malformed_place_id_is_rejected_before_reaching_google():
    app = build().app
    app.dependency_overrides[get_places] = lambda: None  # must never be used
    client = TestClient(app)
    for bad in ("x%3Ffields%3D*", "..%2Fsecret", "a b"):
        resp = client.get(f"/api/places/cities/{bad}?session_token={TOKEN}")
        assert resp.status_code in (404, 422), bad
