from datetime import UTC, datetime

import pytest
from api.sessions.retention import purge_expired_sessions


class FakeResult:
    rowcount = 3


class FakeDb:
    def __init__(self) -> None:
        self.statements: list = []
        self.commits = 0

    async def execute(self, statement):
        self.statements.append(statement)
        return FakeResult()

    async def commit(self) -> None:
        self.commits += 1


@pytest.mark.anyio
async def test_purge_deletes_sessions_older_than_the_retention_period():
    db = FakeDb()
    removed = await purge_expired_sessions(
        db, days=30, now=datetime(2026, 11, 14, 12, 0, tzinfo=UTC)
    )
    assert removed == 3
    assert db.commits == 1
    [statement] = db.statements
    assert statement.is_delete
    # Created before this instant means older than 30 days.
    assert list(statement.compile().params.values()) == [datetime(2026, 10, 15, 12, 0, tzinfo=UTC)]
