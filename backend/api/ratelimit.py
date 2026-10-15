"""In-memory rate limiting for the endpoints that cost money or write rows.

Counters live in this process, which is correct because the service runs exactly one instance
(see CLAUDE.md "Deploy constraint"). Limits come from `Settings`; a limit of 0 turns it off.
"""

import time
from collections import deque
from collections.abc import Callable

from fastapi import HTTPException, Request

from api.sessions.cache import TTL_SECONDS

IP_WINDOW_SECONDS = 60
# A per-session cap covers the life of the session's results, so it uses the cache lifetime.
SESSION_WINDOW_SECONDS = TTL_SECONDS
# Bounds memory when many distinct clients show up; expired keys are dropped first.
MAX_KEYS = 50_000


class RateLimiter:
    """Sliding-window counter per key."""

    def __init__(
        self, clock: Callable[[], float] = time.monotonic, max_keys: int = MAX_KEYS
    ) -> None:
        self._clock = clock
        self._max_keys = max_keys
        self._hits: dict[str, deque[float]] = {}
        self._expires: dict[str, float] = {}

    def hit(self, key: str, limit: int, window_s: float) -> float | None:
        """Count one request. Returns None if allowed, else the seconds until it would be."""
        if limit <= 0:
            return None
        now = self._clock()
        hits = self._hits.get(key)
        if hits is None:
            self._make_room(now)
            hits = self._hits[key] = deque()
        while hits and hits[0] <= now - window_s:
            hits.popleft()
        if len(hits) >= limit:
            return hits[0] + window_s - now
        hits.append(now)
        self._expires[key] = now + window_s
        return None

    def _make_room(self, now: float) -> None:
        if len(self._hits) < self._max_keys:
            return
        for key in [k for k, expiry in self._expires.items() if expiry <= now]:
            del self._hits[key], self._expires[key]
        if len(self._hits) >= self._max_keys:  # all still live: drop the oldest key
            oldest = next(iter(self._hits))
            del self._hits[oldest], self._expires[oldest]


def client_ip(request: Request) -> str:
    # Behind Cloud Run, uvicorn's --proxy-headers makes this the real client address.
    return request.client.host if request.client else "unknown"


def rate_limit(bucket: str, ip_setting: str, session_setting: str | None = None):
    """Route dependency: limits per client IP (per minute) and optionally per session.

    `ip_setting` and `session_setting` name fields on `Settings`.
    """

    def check(request: Request) -> None:
        settings = request.app.state.settings
        limiter: RateLimiter = request.app.state.limiter
        retry_after = limiter.hit(
            f"{bucket}:ip:{client_ip(request)}", getattr(settings, ip_setting), IP_WINDOW_SECONDS
        )
        if retry_after is None and session_setting is not None:
            session_id = request.path_params["session_id"]
            retry_after = limiter.hit(
                f"{bucket}:session:{session_id}",
                getattr(settings, session_setting),
                SESSION_WINDOW_SECONDS,
            )
        if retry_after is not None:
            raise HTTPException(
                status_code=429,
                detail="Too many requests",
                headers={"Retry-After": str(int(retry_after) + 1)},
            )

    return check
