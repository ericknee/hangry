from api.config import Settings
from api.deps import get_candidate_cache, get_places
from api.main import create_app
from api.ratelimit import RateLimiter, client_ip
from api.sessions.cache import CandidateCache
from fastapi import Request
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


def test_limiter_evicts_the_least_recently_used_key_when_full():
    limiter = RateLimiter(clock=lambda: 0.0, max_keys=2)
    limiter.hit("a", 1, 60)
    limiter.hit("b", 1, 60)
    assert limiter.hit("a", 1, 60) is not None  # rejected, but "a" is now more recent than "b"
    limiter.hit("c", 1, 60)  # full: evicts "b", not "a"
    assert limiter.hit("a", 1, 60) is not None  # still limited
    assert limiter.hit("b", 1, 60) is None  # forgotten, starts fresh


def test_limiter_reclaims_expired_keys_even_when_not_full():
    now = [0.0]
    limiter = RateLimiter(clock=lambda: now[0], max_keys=100)
    limiter.hit("old1", 1, 10)
    limiter.hit("old2", 1, 10)
    limiter.hit("live", 1, 60)
    now[0] = 20  # old1 and old2 expired
    limiter.hit("new", 1, 60)
    assert list(limiter._entries) == ["live", "new"]


def test_refund_that_empties_a_key_does_not_break_eviction():
    limiter = RateLimiter(clock=lambda: 0.0, max_keys=2)
    limiter.hit("a", 1, 60)
    limiter.refund("a")
    limiter.hit("b", 1, 60)
    limiter.hit("c", 1, 60)  # full: must evict without touching an empty deque
    assert limiter.hit("c", 1, 60) is not None


def test_empty_entry_is_treated_as_expired():
    limiter = RateLimiter(clock=lambda: 0.0, max_keys=100)
    limiter.hit("a", 1, 60)
    limiter._entries["a"].hits.clear()
    limiter.hit("b", 1, 60)  # would raise IndexError on hits[-1]
    assert "a" not in limiter._entries


def test_client_ip_warns_once_when_forwarded_for_is_shorter_than_proxy_count(caplog):
    from api import ratelimit

    ratelimit._warned.clear()
    app = build(trusted_proxy_count=2).app

    @app.get("/_ip")
    def ip(request: Request) -> str:
        return client_ip(request)

    client = TestClient(app)
    with caplog.at_level("WARNING", logger="api.ratelimit"):
        client.get("/_ip", headers={"X-Forwarded-For": "1.1.1.1"})
        client.get("/_ip", headers={"X-Forwarded-For": "1.1.1.1"})
    assert len([r for r in caplog.records if "TRUSTED_PROXY_COUNT" in r.getMessage()]) == 1


def test_requests_over_the_ip_limit_get_429_with_retry_after():
    client = build(rate_limit_autocomplete_ip_per_min=3)
    url = f"/api/places/autocomplete?input=sa&session_token={TOKEN}"
    # Validation passes but there is no Places client in this app (lifespan not run), so the
    # handler errors with 500; what matters is that the 4th request never reaches it.
    client = TestClient(client.app, raise_server_exceptions=False)
    statuses = [client.get(url).status_code for _ in range(4)]
    assert statuses[:3] != [429] * 3 and 429 not in statuses[:3]
    assert statuses[3] == 429
    assert int(client.get(url).headers["retry-after"]) >= 1


def test_autocomplete_limit_does_not_block_the_city_lookup():
    app = build(rate_limit_autocomplete_ip_per_min=1, rate_limit_city_lookup_ip_per_min=5).app
    client = TestClient(app, raise_server_exceptions=False)
    auto = f"/api/places/autocomplete?input=sa&session_token={TOKEN}"
    lookup = f"/api/places/cities/abc?session_token={TOKEN}"
    client.get(auto)
    assert client.get(auto).status_code == 429
    assert client.get(lookup).status_code != 429


def test_per_session_limit_applies_across_ips_and_is_independent_per_session():
    app = build(rate_limit_photo_ip_per_min=0, rate_limit_photo_session=2).app
    cache = CandidateCache()
    cache.set("s1", [])
    cache.set("s2", [])
    app.dependency_overrides[get_candidate_cache] = lambda: cache
    client = TestClient(app, raise_server_exceptions=False)

    def photo(session: str) -> int:
        return client.get(f"/api/sessions/{session}/restaurants/p1/photo").status_code

    assert 429 not in (photo("s1"), photo("s1"))
    assert photo("s1") == 429
    assert photo("s2") != 429


def test_session_rejection_does_not_use_up_the_shared_ip_quota():
    app = build(rate_limit_photo_ip_per_min=3, rate_limit_photo_session=1).app
    cache = CandidateCache()
    cache.set("s1", [])
    cache.set("s2", [])
    app.dependency_overrides[get_candidate_cache] = lambda: cache
    client = TestClient(app, raise_server_exceptions=False)

    def photo(session: str) -> int:
        return client.get(f"/api/sessions/{session}/restaurants/p1/photo").status_code

    assert photo("s1") != 429  # 1 of 3 IP hits
    assert [photo("s1") for _ in range(5)] == [429] * 5  # rejected by the session, not the IP
    assert photo("s2") != 429  # the IP still has room for another session


def test_session_limit_is_not_reachable_with_ids_that_were_never_issued():
    app = build(rate_limit_photo_ip_per_min=0, rate_limit_photo_session=1).app
    app.dependency_overrides[get_candidate_cache] = lambda: CandidateCache()
    client = TestClient(app, raise_server_exceptions=False)
    statuses = [
        client.get(f"/api/sessions/made-up-{i}/restaurants/p1/photo").status_code for i in range(3)
    ]
    assert statuses == [404, 404, 404]
    assert not app.state.limiter._entries  # nothing was counted for the invented ids


def test_client_ip_ignores_forged_left_side_of_forwarded_for():
    app = build(trusted_proxy_count=2).app

    @app.get("/_ip")
    def ip(request: Request) -> str:
        return client_ip(request)

    client = TestClient(app)
    # Client sent "forged"; Cloudflare appended the visitor, Cloud Run appended Cloudflare.
    headers = {"X-Forwarded-For": "forged, 9.9.9.9, 10.0.0.1"}
    assert client.get("/_ip", headers=headers).json() == "9.9.9.9"
    # Header shorter than the proxy count: use the direct peer rather than a forgeable entry.
    assert client.get("/_ip", headers={"X-Forwarded-For": "forged"}).json() == "testclient"
    assert client.get("/_ip").json() == "testclient"


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
