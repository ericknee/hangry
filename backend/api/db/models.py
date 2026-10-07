"""Phase-1 scope: session logs only. pgvector / taste-embedding tables land
later, behind the embedding stretch goal (see project doc, "APIs & feasibility").
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SessionRecord(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    mode: Mapped[str] = mapped_column(String)  # "solo" | "group"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    state: Mapped[dict] = mapped_column(JSON)  # last-known HangryState snapshot
    final_pick_place_id: Mapped[str | None] = mapped_column(String, nullable=True)
