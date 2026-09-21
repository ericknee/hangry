import uuid

from agent.graph import build_graph
from fastapi import APIRouter

from api.schemas.session import CreateSessionRequest, SessionResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])

_graph = build_graph()


@router.post("", response_model=SessionResponse)
async def create_session(payload: CreateSessionRequest) -> SessionResponse:
    session_id = str(uuid.uuid4())
    # TODO Phase 1: persist a SessionRecord row, then invoke `_graph` with an
    # initial TableTalkState built from `payload`.
    return SessionResponse(
        session_id=session_id,
        mode=payload.mode,
        share_url=f"/join/{session_id}" if payload.mode == "group" else None,
    )
