"""The group endpoints end to end, with a real Postgres database and a fake Places client."""

import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest_asyncio
from api.db.database import get_db
from api.deps import (
    get_candidate_cache,
    get_event_hub,
    get_places,
    get_session_factory,
    get_start_guard,
)
from api.main import app
from api.routers.groups_router import _event_stream
from api.services import groups_service
from api.utils.candidate_cache import CandidateCache
from api.utils.event_hub import EventHub
from api.utils.start_guard import StartGuard
from fakes import PLACE, SETUP
from httpx import ASGITransport, AsyncClient

HERE = {"lat": 37.775, "lng": -122.419}


def place(place_id: str) -> dict:
    return {**PLACE, "id": place_id, "displayName": {"text": place_id}}


class QueryPlaces:
    """Answers a Places text search by the words in the query; records every query."""

    def __init__(self, by_word: dict[str, list[dict]]) -> None:
        self.by_word = by_word
        self.queries: list[str] = []
        self.fail_on: str | None = None

    async def search_text(self, query: str, **kwargs):
        self.queries.append(query.lower())
        if self.fail_on and self.fail_on in query.lower():
            raise httpx.ConnectError("boom")
        for word, results in self.by_word.items():
            if word in query.lower():
                return results
        return []

    @property
    def distinct_queries(self) -> set[str]:
        return set(self.queries)


@pytest_asyncio.fixture
async def api(pg_sessions):
    cache, hub, guard = CandidateCache(), EventHub(), StartGuard()
    places = QueryPlaces(
        {
            "tacos": [place("t1"), place("t2")],
            "sushi": [place("s1"), place("t2")],
            "many": [{**place(f"m{i}"), "rating": 5.0 - i / 10} for i in range(15)],
        }
    )

    async def db():
        async with pg_sessions() as session:
            yield session

    app.dependency_overrides.update(
        {
            get_db: db,
            get_places: lambda: places,
            get_candidate_cache: lambda: cache,
            get_event_hub: lambda: hub,
            get_start_guard: lambda: guard,
            get_session_factory: lambda: pg_sessions,
        }
    )
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield SimpleNamespace(
                client=client,
                cache=cache,
                hub=hub,
                guard=guard,
                places=places,
                sessions=pg_sessions,
            )
    finally:
        app.dependency_overrides.clear()


def as_member(participant_id: str) -> dict:
    return {"X-Participant-Id": participant_id}


async def create_group(api, craving="tacos", name="Host") -> tuple[str, str]:
    resp = await api.client.post(
        "/api/sessions",
        json={"mode": "group", "initial_query": craving, "location": HERE, "name": name},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["share_url"] == f"/join/{body['session_id']}"
    return body["session_id"], body["participant_id"]


async def join(api, sid, name=None, craving=None) -> str:
    resp = await api.client.post(
        f"/api/sessions/{sid}/join", json={"name": name, "craving": craving}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["participant_id"]


async def start(api, sid, host):
    return await api.client.post(f"/api/sessions/{sid}/start", json=SETUP, headers=as_member(host))


async def status(api, sid, pid) -> dict:
    resp = await api.client.get(f"/api/sessions/{sid}/group", headers=as_member(pid))
    assert resp.status_code == 200, resp.text
    return resp.json()


async def deck(api, sid) -> list[str]:
    resp = await api.client.get(f"/api/sessions/{sid}/results")
    return [r["place_id"] for r in resp.json()["restaurants"]]


async def vote(api, sid, pid, values: dict[str, int]):
    votes = [{"place_id": p, "value": v} for p, v in values.items()]
    return await api.client.post(
        f"/api/sessions/{sid}/votes", json={"votes": votes}, headers=as_member(pid)
    )


async def test_solo_sessions_get_no_participant(api):
    resp = await api.client.post(
        "/api/sessions", json={"mode": "solo", "initial_query": "", "location": HERE}
    )
    assert resp.json()["participant_id"] is None


async def test_full_group_flow_ends_with_the_most_liked_place(api):
    sid, host = await create_group(api, craving="tacos")
    guest = await join(api, sid, name="Sam", craving="sushi")

    lobby = await status(api, sid, host)
    assert lobby["phase"] == "lobby" and lobby["me"]["is_host"]
    assert [m["name"] for m in lobby["members"]] == ["Host", "Sam"]
    assert host not in json.dumps(lobby) and guest not in json.dumps(lobby)  # ids stay private

    resp = await start(api, sid, host)
    assert resp.status_code == 200 and resp.json()["count"] == 3  # t1, t2, s1; t2 is shared
    assert len(api.places.distinct_queries) == 2  # one search per distinct craving
    assert (await status(api, sid, guest))["phase"] == "swiping"
    places = await deck(api, sid)
    assert sorted(places) == ["s1", "t1", "t2"]

    favourite = places[2]  # not the top-ranked one, so the vote decides, not the ranking
    resp = await vote(api, sid, host, {p: 1 if p == favourite else -1 for p in places})
    assert resp.status_code == 200 and resp.json()["phase"] == "swiping"
    assert (await status(api, sid, guest))["members"][0]["submitted"] is True

    resp = await vote(api, sid, guest, {p: 1 if p == favourite else -1 for p in places})
    final = resp.json()
    assert final["phase"] == "done"
    assert final["result"]["winner"]["place_id"] == favourite
    assert final["result"]["no_likes"] is False
    top = final["result"]["tallies"][0]
    assert (top["place_id"], top["likes"], top["liked_by"]) == (favourite, 2, ["Host", "Sam"])


async def test_nobody_liking_anything_is_flagged(api):
    sid, host = await create_group(api)
    await start(api, sid, host)
    places = await deck(api, sid)
    final = (await vote(api, sid, host, dict.fromkeys(places, -1))).json()
    assert final["phase"] == "done" and final["result"]["no_likes"] is True
    assert final["result"]["winner"]["place_id"] == places[0]  # the top-ranked place


async def test_credentials_are_required_and_checked_per_session(api):
    sid, host = await create_group(api)
    _, other_host = await create_group(api)
    url = f"/api/sessions/{sid}/group"
    assert (await api.client.get(url)).status_code == 401
    assert (await api.client.get(url, headers=as_member("nope"))).status_code == 403
    assert (await api.client.get(url, headers=as_member(other_host))).status_code == 403
    assert (await api.client.get(url, headers=as_member(host))).status_code == 200
    unknown = await api.client.get("/api/sessions/missing/group", headers=as_member(host))
    assert unknown.status_code == 404


async def test_only_the_host_can_start_or_end(api):
    sid, host = await create_group(api)
    guest = await join(api, sid)
    assert (await start(api, sid, guest)).status_code == 403
    assert (await start(api, sid, host)).status_code == 200
    resp = await api.client.post(f"/api/sessions/{sid}/end", headers=as_member(guest))
    assert resp.status_code == 403


async def test_nobody_can_join_or_edit_after_start_and_the_group_caps_at_eight(api):
    sid, host = await create_group(api)
    for i in range(7):
        await join(api, sid, name=f"g{i}")
    resp = await api.client.post(f"/api/sessions/{sid}/join", json={})
    assert resp.status_code == 409 and "full" in resp.json()["detail"]
    await start(api, sid, host)
    resp = await api.client.post(f"/api/sessions/{sid}/join", json={})
    assert resp.status_code == 409
    resp = await api.client.patch(
        f"/api/sessions/{sid}/me", json={"craving": "x"}, headers=as_member(host)
    )
    assert resp.status_code == 409


async def test_lobby_edits_change_name_and_craving(api):
    sid, _ = await create_group(api, name="Sam")
    guest = await join(api, sid, name="Sam", craving="pizza")  # clashes: becomes "Sam 2"
    resp = await api.client.patch(
        f"/api/sessions/{sid}/me", json={"craving": "  sushi "}, headers=as_member(guest)
    )
    assert resp.json() == {
        "name": "Sam 2",
        "craving": "sushi",
        "is_host": False,
        "submitted": False,
    }


async def test_votes_must_cover_the_deck_exactly_and_only_once(api):
    sid, host = await create_group(api)
    await start(api, sid, host)
    places = await deck(api, sid)
    assert (await vote(api, sid, host, {places[0]: 1})).status_code == 400  # incomplete
    extra = await vote(api, sid, host, {**dict.fromkeys(places, 1), "extra": 1})
    assert extra.status_code == 400
    dup = [{"place_id": places[0], "value": 1}] * len(places)
    resp = await api.client.post(
        f"/api/sessions/{sid}/votes", json={"votes": dup}, headers=as_member(host)
    )
    assert resp.status_code == 400
    zero = await vote(api, sid, host, dict.fromkeys(places, 0))
    assert zero.status_code == 422  # clients cannot send "no vote"
    assert (await vote(api, sid, host, dict.fromkeys(places, 1))).status_code == 200
    assert (await vote(api, sid, host, dict.fromkeys(places, 1))).status_code == 409


async def test_votes_before_start_are_rejected(api):
    sid, host = await create_group(api)
    resp = await api.client.post(
        f"/api/sessions/{sid}/votes", json={"votes": []}, headers=as_member(host)
    )
    assert resp.status_code == 404  # no shortlist yet


async def test_host_ending_early_gives_everyone_else_no_votes(api):
    sid, host = await create_group(api)
    guest = await join(api, sid, name="Slow")
    await start(api, sid, host)
    places = await deck(api, sid)
    await vote(api, sid, host, {p: 1 if p == places[1] else -1 for p in places})

    resp = await api.client.post(f"/api/sessions/{sid}/end", headers=as_member(host))
    final = resp.json()
    assert final["phase"] == "done"
    assert final["result"]["winner"]["place_id"] == places[1]
    assert all(m["submitted"] for m in final["members"])
    assert all("Slow" not in t["liked_by"] + t["disliked_by"] for t in final["result"]["tallies"])
    # The slow member's late submit is refused: swiping is over.
    assert (await vote(api, sid, guest, dict.fromkeys(places, 1))).status_code == 409


async def test_failed_start_keeps_the_lobby_and_a_retry_only_repeats_what_failed(api):
    sid, host = await create_group(api, craving="tacos")
    await join(api, sid, craving="sushi")
    api.places.fail_on = "sushi"
    resp = await start(api, sid, host)
    assert resp.status_code == 502
    assert (await status(api, sid, host))["phase"] == "lobby"
    assert not api.guard.is_active(sid)

    api.places.fail_on = None
    api.places.queries.clear()
    assert (await start(api, sid, host)).status_code == 200
    assert not any("tacos" in q for q in api.places.queries)  # tacos was kept from the first try
    assert (await status(api, sid, host))["phase"] == "swiping"


async def test_the_group_deck_is_the_best_twelve_of_the_merged_pool(api):
    sid, host = await create_group(api, craving="many")
    resp = await start(api, sid, host)
    assert resp.json()["count"] == groups_service.GROUP_DECK_SIZE == 12
    places = await deck(api, sid)
    assert len(places) == 12
    assert places[0] == "m0" and "m14" not in places  # the best are kept, the worst cut
    # A submit has to cover exactly these twelve.
    assert (await vote(api, sid, host, dict.fromkeys(places, 1))).status_code == 200


async def test_start_with_no_places_stays_in_the_lobby(api):
    sid, host = await create_group(api, craving="nothing matches this")
    resp = await start(api, sid, host)
    assert resp.status_code == 200 and resp.json()["count"] == 0
    assert (await status(api, sid, host))["phase"] == "lobby"


async def test_a_second_start_or_join_while_one_runs_is_refused(api):
    sid, host = await create_group(api)
    assert api.guard.try_acquire(sid)  # as if the host's searches were running
    assert (await start(api, sid, host)).status_code == 409
    assert (await api.client.post(f"/api/sessions/{sid}/join", json={})).status_code == 409
    api.guard.release(sid)
    assert (await start(api, sid, host)).status_code == 200


async def test_solo_sessions_cannot_be_joined(api):
    resp = await api.client.post(
        "/api/sessions", json={"mode": "solo", "initial_query": "", "location": HERE}
    )
    sid = resp.json()["session_id"]
    assert (await api.client.post(f"/api/sessions/{sid}/join", json={})).status_code == 404


async def next_event(stream) -> dict:
    """The next `status` event from the stream, skipping the retry hint and keepalives."""
    while True:
        chunk = await asyncio.wait_for(anext(stream), timeout=2)
        if chunk.startswith("event: status"):
            return json.loads(chunk.split("data: ", 1)[1])


async def test_event_stream_sends_a_snapshot_then_one_per_change(api):
    sid, host = await create_group(api)
    stream = _event_stream(api.sessions, api.cache, api.hub, sid, host)
    first = await next_event(stream)
    assert [m["name"] for m in first["members"]] == ["Host"]

    await join(api, sid, name="Sam")
    api.hub.notify(sid)  # the router does this after a join
    second = await next_event(stream)
    assert [m["name"] for m in second["members"]] == ["Host", "Sam"]
    await stream.aclose()
    api.hub.notify(sid)  # nobody is listening any more: no error


async def test_a_newer_stream_for_the_same_member_ends_the_old_one(api):
    sid, host = await create_group(api)
    old = _event_stream(api.sessions, api.cache, api.hub, sid, host)
    await next_event(old)
    new = _event_stream(api.sessions, api.cache, api.hub, sid, host)
    await next_event(new)
    chunks = [c async for c in old]  # drains and stops instead of waiting forever
    assert all(not c.startswith("event: status") for c in chunks)
    await new.aclose()


async def test_events_endpoint_rejects_unknown_members(api):
    sid, _ = await create_group(api)
    resp = await api.client.get(f"/api/sessions/{sid}/events", params={"participant_id": "nope"})
    assert resp.status_code == 403
