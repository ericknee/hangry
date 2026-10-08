"""Helpers for passing media from an upstream service through to the browser."""

import httpx
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask


def stream_upstream(upstream: httpx.Response, *, max_age_s: int) -> StreamingResponse:
    """Relay an open streamed upstream response; it is closed once the body has been sent.

    `private` keeps shared proxies from storing it; the browser may reuse it for `max_age_s`.
    """
    return StreamingResponse(
        upstream.aiter_raw(),
        media_type=upstream.headers.get("content-type", "application/octet-stream"),
        headers={"Cache-Control": f"private, max-age={max_age_s}"},
        background=BackgroundTask(upstream.aclose),
    )
