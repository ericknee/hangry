"""Serves the built React app from the same process as the API.

Same origin means the browser needs no CORS and the client can call `/api/...` as a relative URL.
Page routes such as `/privacy` or `/session/<id>/shortlist` are client-side, so any path that is not
a real file falls back to `index.html` and react-router takes over.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

# Vite writes content-hashed filenames into assets/, so they can be cached forever. index.html names
# those files, so it must be revalidated or a deploy would leave browsers on stale pages.
IMMUTABLE = "public, max-age=31536000, immutable"
NO_CACHE = "no-cache"


def mount_frontend(app: FastAPI, static_dir: Path, *, api_prefix: str) -> None:
    """Add a catch-all GET route. Call it after every API route is registered."""
    root = static_dir.resolve()
    index = root / "index.html"
    if not index.is_file():
        raise RuntimeError(f"STATIC_DIR {root} has no index.html; run `npm run build` in client/")

    @app.get("/{path:path}", include_in_schema=False)
    async def frontend(path: str) -> FileResponse:
        # Unknown API paths stay JSON 404s instead of returning the HTML page.
        if path == api_prefix.strip("/") or path.startswith(api_prefix.strip("/") + "/"):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = (root / path).resolve()
        # resolve() collapses "..", so this also blocks reading files outside the folder.
        if candidate.is_file() and candidate.is_relative_to(root):
            is_asset = candidate.is_relative_to(root / "assets")
            return FileResponse(
                candidate, headers={"Cache-Control": IMMUTABLE if is_asset else NO_CACHE}
            )
        return FileResponse(index, headers={"Cache-Control": NO_CACHE})
