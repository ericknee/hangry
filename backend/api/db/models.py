"""Phase-1 scope: session logs only. pgvector / taste-embedding tables land
later, behind the embedding stretch goal (see project doc, "APIs & feasibility").
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SessionRecord(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    mode: Mapped[str] = mapped_column(String)  # "solo" | "group"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    state: Mapped[dict] = mapped_column(JSON)  # last-known HangryState snapshot
    final_pick_place_id: Mapped[str | None] = mapped_column(String, nullable=True)
    # Group sessions only: "setup" -> "lobby" -> "swiping" -> "done". Solo sessions stay at "setup".
    phase: Mapped[str] = mapped_column(String, default="setup", server_default="setup")


class ParticipantRecord(Base):
    """A member of a group session. The host is a participant too.

    `id` doubles as the credential the browser keeps: it is random and unguessable, so it must
    never appear in a response that other members can read.
    """

    __tablename__ = "participants"
    __table_args__ = (UniqueConstraint("session_id", "name"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(
        String, ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(30))  # unique per session; a clash gets a suffix
    is_host: Mapped[bool] = mapped_column(Boolean, default=False)
    craving: Mapped[str | None] = mapped_column(String(100), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    # Set on submit, or for everyone still swiping when the host ends early (those have no votes).
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class VoteRecord(Base):
    """One member's like or dislike of one place. Holds the place id only, never Places content."""

    __tablename__ = "votes"

    participant_id: Mapped[str] = mapped_column(
        String, ForeignKey("participants.id", ondelete="CASCADE"), primary_key=True
    )
    place_id: Mapped[str] = mapped_column(String, primary_key=True)
    # > 0 like, < 0 dislike, 0 no vote (only when the host ends early). The UI sends -1 or 1 today;
    # larger magnitudes are reserved for strengths, so the service validates the range.
    value: Mapped[int] = mapped_column(Integer)
