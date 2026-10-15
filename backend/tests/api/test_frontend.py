from api.config import Settings
from api.main import create_app
from fastapi.testclient import TestClient


def build(tmp_path) -> TestClient:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>app</html>", encoding="utf-8")
    (tmp_path / "assets" / "app-abc123.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path.parent / "secret.txt").write_text("secret", encoding="utf-8")
    settings = Settings(database_url="x", google_places_api_key="x", static_dir=tmp_path)
    return TestClient(create_app(settings))


def test_page_routes_fall_back_to_index_html(tmp_path):
    client = build(tmp_path)
    for path in ("/", "/privacy", "/session/abc/shortlist"):
        resp = client.get(path)
        assert resp.status_code == 200, path
        assert resp.text == "<html>app</html>"
        assert resp.headers["cache-control"] == "no-cache"


def test_hashed_assets_are_cached_forever(tmp_path):
    resp = build(tmp_path).get("/assets/app-abc123.js")
    assert resp.status_code == 200
    assert "immutable" in resp.headers["cache-control"]


def test_unknown_api_paths_are_json_404s_not_the_html_page(tmp_path):
    client = build(tmp_path)
    for path in ("/api/nope", "/api"):
        resp = client.get(path)
        assert resp.status_code == 404, path
        assert resp.json() == {"detail": "Not Found"}
    assert client.get("/api/health").json() == {"status": "ok"}


def test_paths_cannot_escape_the_static_folder(tmp_path):
    resp = build(tmp_path).get("/..%2Fsecret.txt")
    assert resp.text == "<html>app</html>"


def test_no_frontend_routes_without_static_dir():
    settings = Settings(database_url="x", google_places_api_key="x")
    assert TestClient(create_app(settings)).get("/privacy").status_code == 404
