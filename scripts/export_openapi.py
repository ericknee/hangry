"""Write the FastAPI app's OpenAPI schema to client/src/api/openapi.json.

Run via `npm run gen:api` from client/, which then turns it into TypeScript types. The schema
is the contract between backend and client; backend/tests/api/test_openapi_snapshot.py fails
when this file is out of date.
"""

import json
import os
from pathlib import Path

# Importing the app builds its settings; the real values are irrelevant for a schema dump.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://schema:schema@localhost:5432/schema")
os.environ.setdefault("GOOGLE_PLACES_API_KEY", "schema-export")

from api.main import app  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "client" / "src" / "api" / "openapi.json"

if __name__ == "__main__":
    OUT.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
