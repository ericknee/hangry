import httpx
import pytest
from api.utils.media import _relay_body


def upstream() -> httpx.Response:
    return httpx.Response(200, stream=httpx.ByteStream(b"abcdef"))


@pytest.mark.anyio
async def test_relay_closes_upstream_after_full_body():
    resp = upstream()
    assert b"".join([c async for c in _relay_body(resp)]) == b"abcdef"
    assert resp.is_closed


@pytest.mark.anyio
async def test_relay_closes_upstream_when_consumer_stops_early():
    resp = upstream()
    gen = _relay_body(resp)
    await anext(gen)
    await gen.aclose()  # what cancellation on browser disconnect amounts to
    assert resp.is_closed
