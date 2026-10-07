from api.sessions.cache import CandidateCache


def test_cache_entries_expire():
    now = [0.0]
    cache = CandidateCache(ttl_seconds=10, clock=lambda: now[0])
    cache.set("s1", [])
    assert cache.get("s1") == []
    now[0] = 11.0
    assert cache.get("s1") is None
