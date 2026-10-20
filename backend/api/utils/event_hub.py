"""Wakes the open event streams of a group session when its state changes.

In-memory, which is correct because the service runs exactly one instance (see CLAUDE.md "Deploy
constraint"). A stream only needs to know that something changed; it then reads the current state
from the database, so a missed or merged wake-up never loses information.
"""

import asyncio

CHANGED = object()  # something in the session changed: send a fresh snapshot
CLOSED = object()  # this stream was replaced by a newer one from the same member


class EventHub:
    def __init__(self) -> None:
        self._streams: dict[str, dict[str, asyncio.Queue]] = {}

    def subscribe(self, session_id: str, participant_id: str) -> asyncio.Queue:
        """A member has one stream; opening another (a reconnect) closes the old one."""
        streams = self._streams.setdefault(session_id, {})
        old = streams.get(participant_id)
        if old is not None:
            while not old.empty():
                old.get_nowait()
            old.put_nowait(CLOSED)
        queue: asyncio.Queue = asyncio.Queue(maxsize=1)  # a pending wake-up already says "changed"
        streams[participant_id] = queue
        return queue

    def unsubscribe(self, session_id: str, participant_id: str, queue: asyncio.Queue) -> None:
        streams = self._streams.get(session_id)
        if streams is not None and streams.get(participant_id) is queue:
            del streams[participant_id]
            if not streams:
                del self._streams[session_id]

    def notify(self, session_id: str) -> None:
        for queue in self._streams.get(session_id, {}).values():
            try:
                queue.put_nowait(CHANGED)
            except asyncio.QueueFull:
                pass  # a wake-up is already waiting
