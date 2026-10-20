"""group sessions: participants, votes and a session phase

Both new tables get row level security with no policies, like sessions (0002). Deleting a session
cascades to its participants and their votes, so the daily purge needs no changes.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sessions", sa.Column("phase", sa.String(), nullable=False, server_default="setup")
    )

    op.create_table(
        "participants",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(30), nullable=False),
        sa.Column("is_host", sa.Boolean(), nullable=False),
        sa.Column("craving", sa.String(100), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("session_id", "name"),
    )
    op.create_index("ix_participants_session_id", "participants", ["session_id"])

    op.create_table(
        "votes",
        sa.Column(
            "participant_id",
            sa.String(),
            sa.ForeignKey("participants.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("place_id", sa.String(), primary_key=True),
        sa.Column("value", sa.Integer(), nullable=False),
    )

    op.execute("ALTER TABLE participants ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE votes ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_table("votes")
    op.drop_index("ix_participants_session_id", table_name="participants")
    op.drop_table("participants")
    op.drop_column("sessions", "phase")
