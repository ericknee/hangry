"""enable row level security on sessions

Supabase exposes every table in the public schema through its own REST API. With row level
security on and no policies, that API (the `anon` and `authenticated` roles) can read and write
nothing. The backend connects as the table owner, which is not subject to RLS, so it is unaffected.
On plain Postgres this is a harmless no-op.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-14
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE sessions ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("ALTER TABLE sessions DISABLE ROW LEVEL SECURITY")
