"""Helpers for passing media from an upstream service through to the browser."""

from collections.abc import AsyncIterator

import httpx
from fastapi.responses import StreamingResponse


async def _relay_body(upstream: httpx.Response) -> AsyncIterator[bytes]:
    # Closing in `finally` (not a BackgroundTask) also covers the browser aborting mid-stream,
    # where Starlette cancels the response and skips background tasks.
    try:
        # aiter_bytes decodes, since Content-Encoding is not forwarded
        async for chunk in upstream.aiter_bytes():
            yield chunk
    finally:
        await upstream.aclose()


def stream_upstream(upstream: httpx.Response, *, max_age_s: int) -> StreamingResponse:
    """Relay an open streamed upstream response; it is closed when the body ends or is cancelled.

    `private` keeps shared proxies from storing it; the browser may reuse it for `max_age_s`.
    """
    return StreamingResponse(
        _relay_body(upstream),
        media_type=upstream.headers.get("content-type", "application/octet-stream"),
        headers={"Cache-Control": f"private, max-age={max_age_s}"},
    )
