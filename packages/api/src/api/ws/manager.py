"""Broadcasts live updates to every member of a group session (e.g. "2 of 3
members have finished elicitation") as the parallel elicit branches complete.
"""

from __future__ import annotations

from fastapi import WebSocket


class SessionConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, session_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(session_id, []).append(ws)

    def disconnect(self, session_id: str, ws: WebSocket) -> None:
        if session_id in self._connections:
            self._connections[session_id].remove(ws)

    async def broadcast(self, session_id: str, message: dict) -> None:
        for ws in self._connections.get(session_id, []):
            await ws.send_json(message)


manager = SessionConnectionManager()
