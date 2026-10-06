import time
from collections.abc import Callable

from agent.state import Candidate
from fastapi import Request

TTL_SECONDS = 30 * 60


class CandidateCache:
    """In-memory, short-lived candidate storage keyed by session id.

    Google's terms limit how long Places content may be kept, so candidates live here
    for `ttl_seconds` and are lost on restart; the database only keeps IDs and picks.
    """

    def __init__(
        self, ttl_seconds: float = TTL_SECONDS, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._ttl = ttl_seconds
        self._clock = clock
        self._items: dict[str, tuple[float, list[Candidate]]] = {}

    def set(self, session_id: str, candidates: list[Candidate]) -> None:
        now = self._clock()
        self._items = {k: v for k, v in self._items.items() if v[0] > now}  # drop expired
        self._items[session_id] = (now + self._ttl, candidates)

    def get(self, session_id: str) -> list[Candidate] | None:
        item = self._items.get(session_id)
        if item is None:
            return None
        if item[0] <= self._clock():
            del self._items[session_id]
            return None
        return item[1]


def get_candidate_cache(request: Request) -> CandidateCache:
    """The app-wide cache created in `main.lifespan`."""
    return request.app.state.candidates
