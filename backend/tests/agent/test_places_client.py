import json

import httpx
import pytest
from agent.places_client import PlacesClient


def client_with(api_json, cdn_response: httpx.Response | None = None) -> PlacesClient:
    client = PlacesClient("key")
    client._http = httpx.AsyncClient(
        base_url="https://places.test",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=api_json)),
    )
    client._media_http = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: cdn_response)
    )
    return client


@pytest.mark.anyio
async def test_open_photo_returns_open_image_stream():
    cdn = httpx.Response(200, headers={"content-type": "image/jpeg"}, content=b"JPEG")
    client = client_with({"photoUri": "https://cdn.test/p.jpg"}, cdn)
    upstream = await client.open_photo("places/p/photos/a", max_width_px=800)
    assert await upstream.aread() == b"JPEG"
    await client.aclose()


@pytest.mark.anyio
@pytest.mark.parametrize("api_json", [{}, {"photoUri": ""}, {"photoUri": 5}, ["not", "a", "dict"]])
async def test_open_photo_without_a_usable_photo_uri_raises_value_error(api_json):
    client = client_with(api_json)
    with pytest.raises(ValueError):
        await client.open_photo("places/p/photos/a", max_width_px=800)
    await client.aclose()


@pytest.mark.anyio
async def test_open_photo_rejects_and_closes_non_image_responses():
    cdn = httpx.Response(200, headers={"content-type": "text/html"}, content=b"<html>")
    client = client_with({"photoUri": "https://cdn.test/p.jpg"}, cdn)
    with pytest.raises(ValueError):
        await client.open_photo("places/p/photos/a", max_width_px=800)
    assert cdn.is_closed
    await client.aclose()


def recording_client(api_json) -> tuple[PlacesClient, list[httpx.Request]]:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=api_json)

    client = PlacesClient("key")
    client._http = httpx.AsyncClient(
        base_url="https://places.test", transport=httpx.MockTransport(handler)
    )
    return client, requests


TOKEN = "3f1c0f0e-8a52-4f0a-9d56-0f2c7d1f5b11"


@pytest.mark.anyio
async def test_autocomplete_sends_the_session_token_only_when_given():
    client, requests = recording_client({"suggestions": []})
    await client.autocomplete_cities("sant", session_token=TOKEN)
    await client.autocomplete_cities("sant")
    assert json.loads(requests[0].content)["sessionToken"] == TOKEN
    assert json.loads(requests[0].content)["includedRegionCodes"] == ["us"]
    assert "sessionToken" not in json.loads(requests[1].content)
    await client.aclose()


@pytest.mark.anyio
async def test_place_location_sends_the_session_token_only_when_given():
    place = {"id": "c1", "location": {"latitude": 1.0, "longitude": 2.0}}
    client, requests = recording_client(place)
    await client.get_place_location("c1", session_token=TOKEN)
    await client.get_place_location("c1")
    assert requests[0].url.params["sessionToken"] == TOKEN
    assert "sessionToken" not in requests[1].url.params
    await client.aclose()
