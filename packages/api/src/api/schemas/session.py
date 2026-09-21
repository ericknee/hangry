from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    mode: str  # "solo" | "group"
    initial_query: str


class SessionResponse(BaseModel):
    session_id: str
    mode: str
    share_url: str | None = None
