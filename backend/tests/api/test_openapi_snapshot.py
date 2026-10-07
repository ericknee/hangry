import json
from pathlib import Path

from api.main import app

SNAPSHOT = Path(__file__).resolve().parents[3] / "client" / "src" / "api" / "openapi.json"


def test_openapi_snapshot_is_current():
    """The client's TypeScript types are generated from this snapshot, so it must match the API."""
    live = json.loads(json.dumps(app.openapi()))
    committed = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert live == committed, (
        "The API's types changed but client/src/api/openapi.json (and types.gen.ts) did not. "
        "Run `npm run gen:api` in client/ and commit the result."
    )
