"""In-memory rate limiting for the endpoints that cost money or write rows.

Counters live in this process, which is correct because the service runs exactly one instance
(see CLAUDE.md "Deploy constraint"). Limits come from `Settings`; a limit of 0 turns it off.
"""

import time
from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass, field

from fastapi import HTTPException, Request

from api.sessions.cache import TTL_SECONDS

IP_WINDOW_SECONDS = 60
# A per-session cap covers the life of the session's results, so it uses the cache lifetime.
SESSION_WINDOW_SECONDS = TTL_SECONDS
# Bounds memory when many distinct clients show up.
MAX_KEYS = 50_000


@dataclass
class _Entry:
    window_s: float  # kept so an idle entry can be recognised as expired without the caller
    hits: deque[float] = field(default_factory=deque)


class RateLimiter:
    """Sliding-window counter per key, evicting the least recently used key when full."""

    def __init__(
        self, clock: Callable[[], float] = time.monotonic, max_keys: int = MAX_KEYS
    ) -> None:
        self._clock = clock
        self._max_keys = max_keys
        # Least recently used first. Evicting by insertion order instead would let a flood of new
        # keys push out the very callers that are being limited and reset their counters.
        self._entries: OrderedDict[str, _Entry] = OrderedDict()

    def hit(self, key: str, limit: int, window_s: float) -> float | None:
        """Count one request. Returns None if allowed, else the seconds until it would be."""
        if limit <= 0:
            return None
        now = self._clock()
        entry = self._entries.get(key)
        if entry is None:
            self._make_room(now)
            entry = self._entries[key] = _Entry(window_s)
        else:
            # Moved even when rejected, so a caller that keeps retrying stays the last to go.
            self._entries.move_to_end(key)
        hits = entry.hits
        while hits and hits[0] <= now - window_s:
            hits.popleft()
        if len(hits) >= limit:
            return hits[0] + window_s - now
        hits.append(now)
        return None

    def refund(self, key: str) -> None:
        """Take back the most recent hit, for a request that another limit then rejected."""
        entry = self._entries.get(key)
        if entry and entry.hits:
            entry.hits.pop()

    def _make_room(self, now: float) -> None:
        # Only the LRU end is inspected: a full scan per new key would make a flood of fake
        # callers slow every request. Expired entries go whenever they reach the front, so
        # memory is reclaimed gradually; a live one goes only if the table is full.
        while self._entries:
            key, entry = next(iter(self._entries.items()))
            expired = entry.hits[-1] + entry.window_s <= now
            if not expired and len(self._entries) < self._max_keys:
                break
            del self._entries[key]


def client_ip(request: Request) -> str:
    """The client address, read from the right of X-Forwarded-For.

    Each trusted proxy appends the address it saw to the end of the header, so everything to the
    left of those entries was written by the client and can be forged. With N trusted proxies the
    real client is the Nth entry from the right. If the header is shorter than that (a request that
    skipped the proxies, or local dev), fall back to the direct peer.
    """
    peer = request.client.host if request.client else "unknown"
    count = request.app.state.settings.trusted_proxy_count
    if count <= 0:
        return peer
    forwarded = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",")]
    forwarded = [p for p in forwarded if p]
    return forwarded[-count] if len(forwarded) >= count else peer


def _reject(retry_after: float) -> HTTPException:
    return HTTPException(
        status_code=429,
        detail="Too many requests",
        headers={"Retry-After": str(int(retry_after) + 1)},
    )


def rate_limit(bucket: str, ip_setting: str):
    """Route dependency: limits requests per client IP (per minute).

    `ip_setting` names a field on `Settings`.
    """

    def check(request: Request) -> None:
        limiter: RateLimiter = request.app.state.limiter
        retry_after = limiter.hit(
            f"{bucket}:ip:{client_ip(request)}",
            getattr(request.app.state.settings, ip_setting),
            IP_WINDOW_SECONDS,
        )
        if retry_after is not None:
            raise _reject(retry_after)

    return check


def session_rate_limit(bucket: str, session_setting: str):
    """Route dependency: limits requests per session over the results lifetime.

    List it after the IP limit and `require_session` / `require_results`: the session id comes
    from the URL, so counting an unchecked one would let a caller dodge the cap by inventing ids.
    """

    def check(request: Request, session_id: str) -> None:
        limiter: RateLimiter = request.app.state.limiter
        retry_after = limiter.hit(
            f"{bucket}:session:{session_id}",
            getattr(request.app.state.settings, session_setting),
            SESSION_WINDOW_SECONDS,
        )
        if retry_after is not None:
            # The IP limit runs first so invented ids cost it a hit. A locked-out session that
            # keeps retrying must not also drain the quota of others behind the same IP.
            limiter.refund(f"{bucket}:ip:{client_ip(request)}")
            raise _reject(retry_after)

    return check
