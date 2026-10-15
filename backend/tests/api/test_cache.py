from api.sessions.cache import CandidateCache


def test_cache_entries_expire():
    now = [0.0]
    cache = CandidateCache(ttl_seconds=10, clock=lambda: now[0])
    cache.set("s1", [])
    assert cache.get("s1") == []
    now[0] = 11.0
    assert cache.get("s1") is None


def test_cache_evicts_the_oldest_entry_when_full():
    now = [0.0]
    cache = CandidateCache(ttl_seconds=100, clock=lambda: now[0], max_entries=2)
    cache.set("s1", [])
    now[0] = 1.0
    cache.set("s2", [])
    now[0] = 2.0
    cache.set("s3", [])
    assert cache.get("s1") is None
    assert cache.get("s2") == []
    assert cache.get("s3") == []


def test_cache_replacing_an_entry_does_not_evict_others():
    now = [0.0]
    cache = CandidateCache(ttl_seconds=100, clock=lambda: now[0], max_entries=2)
    cache.set("s1", [])
    cache.set("s2", [])
    cache.set("s1", [])  # refresh, not growth
    assert cache.get("s2") == []
    cache.set("s3", [])  # now full: s2 is the oldest
    assert cache.get("s2") is None
    assert cache.get("s1") == []
