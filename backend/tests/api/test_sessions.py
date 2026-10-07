from api.db.database import get_db
from api.db.models import SessionRecord
from api.main import app
from fastapi.testclient import TestClient


class FakeDb:
    def __init__(self) -> None:
        self.added: list[SessionRecord] = []
        self.commits = 0

    def add(self, record: SessionRecord) -> None:
        self.added.append(record)

    async def commit(self) -> None:
        self.commits += 1


def post_session(payload: dict) -> tuple[dict, FakeDb]:
    fake = FakeDb()

    async def override():
        yield fake

    app.dependency_overrides[get_db] = override
    try:
        resp = TestClient(app).post("/sessions", json=payload)
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 200
    return resp.json(), fake


def test_create_session_records_row_with_rounded_coordinates():
    body, db = post_session(
        {
            "mode": "solo",
            "initial_query": "tacos",
            "location": {"lat": 37.77493, "lng": -122.41942},  # no place_id: current location
        }
    )
    assert body["share_url"] is None
    assert db.commits == 1
    [record] = db.added
    assert record.id == body["session_id"]
    assert record.mode == "solo"
    assert record.state["initial_query"] == "tacos"
    assert record.state["location"]["lat"] == 37.775
    assert record.state["location"]["lng"] == -122.419


def test_create_session_without_location():
    _, db = post_session({"mode": "solo", "initial_query": ""})
    assert db.added[0].state == {"initial_query": "", "location": None}
