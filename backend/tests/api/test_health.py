from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_docs_are_served_in_dev_but_not_in_prod():
    from api.config import Settings
    from api.main import create_app

    def build(environment: str) -> TestClient:
        settings = Settings(database_url="x", google_places_api_key="x", environment=environment)
        return TestClient(create_app(settings))

    dev, prod = build("dev"), build("prod")
    assert dev.get("/docs").status_code == 200
    assert dev.get("/openapi.json").status_code == 200
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert prod.get(path).status_code == 404, path
    assert prod.get("/api/health").status_code == 200
