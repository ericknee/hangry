"""Remembers which group sessions have a start (the paid searches) in progress.

A second start, or a join or edit that would change the cravings being searched, must wait. In
memory, which is correct because the service runs exactly one instance.
"""


class StartGuard:
    def __init__(self) -> None:
        self._active: set[str] = set()

    def try_acquire(self, session_id: str) -> bool:
        if session_id in self._active:
            return False
        self._active.add(session_id)
        return True

    def release(self, session_id: str) -> None:
        self._active.discard(session_id)

    def is_active(self, session_id: str) -> bool:
        return session_id in self._active
