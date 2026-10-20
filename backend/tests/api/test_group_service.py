"""Group service rules and writes, against a real Postgres database (skipped if unreachable)."""

import asyncio

import pytest
from api.db.models import ParticipantRecord, SessionRecord, VoteRecord
from api.errors.groups_errors import (
    AlreadySubmitted,
    GroupFull,
    NotAGroupSession,
    NotAMember,
    NotInLobby,
    NotSwiping,
)
from api.errors.sessions_errors import SessionNotFound
from api.services import groups_service as svc
from api.types.sessions_types import CreateSessionRequest
from sqlalchemy import func, select

PLACES = ["p1", "p2", "p3"]


async def make_session(sessions, *, mode="group", phase="lobby") -> str:
    async with sessions() as db:
        record = SessionRecord(mode=mode, phase=phase, state={})
        db.add(record)
        await db.commit()
        return record.id


async def join(sessions, session_id, name=None, craving=None, is_host=False):
    async with sessions() as db:
        return await svc.join(db, session_id, name=name, craving=craving, is_host=is_host)


async def count(sessions, model) -> int:
    async with sessions() as db:
        return await db.scalar(select(func.count()).select_from(model))


async def test_join_stores_member_with_trimmed_craving(pg_sessions):
    sid = await make_session(pg_sessions)
    member = await join(pg_sessions, sid, name="Sam", craving="  tacos ", is_host=True)
    assert (member.name, member.craving, member.is_host) == ("Sam", "tacos", True)
    assert member.submitted_at is None and member.id


async def test_blank_craving_is_stored_as_none(pg_sessions):
    sid = await make_session(pg_sessions)
    assert (await join(pg_sessions, sid, craving="  ")).craving is None


async def test_duplicate_names_get_suffixes(pg_sessions):
    sid = await make_session(pg_sessions)
    names = [(await join(pg_sessions, sid, name="Sam")).name for _ in range(3)]
    assert names == ["Sam", "Sam 2", "Sam 3"]


async def test_same_name_in_different_sessions_is_allowed(pg_sessions):
    a, b = await make_session(pg_sessions), await make_session(pg_sessions)
    assert (await join(pg_sessions, a, name="Sam")).name == "Sam"
    assert (await join(pg_sessions, b, name="Sam")).name == "Sam"


async def test_group_is_full_at_eight_members(pg_sessions):
    sid = await make_session(pg_sessions)
    for i in range(svc.MAX_MEMBERS):
        await join(pg_sessions, sid, name=f"m{i}")
    with pytest.raises(GroupFull):
        await join(pg_sessions, sid, name="late")


async def test_concurrent_joins_respect_the_cap_and_unique_names(pg_sessions):
    sid = await make_session(pg_sessions)
    results = await asyncio.gather(
        *(join(pg_sessions, sid, name="Sam") for _ in range(12)), return_exceptions=True
    )
    joined = [r for r in results if not isinstance(r, Exception)]
    assert len(joined) == svc.MAX_MEMBERS
    assert all(isinstance(r, GroupFull) for r in results if isinstance(r, Exception))
    assert len({m.name for m in joined}) == svc.MAX_MEMBERS


async def test_cannot_join_after_start_or_a_solo_or_unknown_session(pg_sessions):
    started = await make_session(pg_sessions, phase="swiping")
    solo = await make_session(pg_sessions, mode="solo", phase="setup")
    with pytest.raises(NotInLobby):
        await join(pg_sessions, started)
    with pytest.raises(NotAGroupSession):
        await join(pg_sessions, solo)
    with pytest.raises(SessionNotFound):
        await join(pg_sessions, "missing")


async def test_update_member_renames_uniquely_and_sets_or_clears_craving(pg_sessions):
    sid = await make_session(pg_sessions)
    await join(pg_sessions, sid, name="Sam")
    other = await join(pg_sessions, sid, name="Alex", craving="pizza")
    async with pg_sessions() as db:
        updated = await svc.update_member(db, sid, other.id, name="Sam", craving="")
    assert (updated.name, updated.craving) == ("Sam 2", None)
    async with pg_sessions() as db:
        kept = await svc.update_member(db, sid, other.id, name="  ", craving=None)
    assert kept.name == "Sam 2"  # a blank name keeps the current one


async def test_renaming_to_your_own_name_does_not_add_a_suffix(pg_sessions):
    sid = await make_session(pg_sessions)
    me = await join(pg_sessions, sid, name="Sam")
    async with pg_sessions() as db:
        assert (await svc.update_member(db, sid, me.id, name="Sam", craving=None)).name == "Sam"


async def test_update_member_rejected_after_start_and_for_a_foreign_member(pg_sessions):
    sid, other_sid = await make_session(pg_sessions), await make_session(pg_sessions)
    me = await join(pg_sessions, sid)
    stranger = await join(pg_sessions, other_sid)
    async with pg_sessions() as db:
        with pytest.raises(NotAMember):
            await svc.update_member(db, sid, stranger.id, name="x", craving=None)
    async with pg_sessions() as db:
        await svc.begin_swiping(db, sid)
    async with pg_sessions() as db:
        with pytest.raises(NotInLobby):
            await svc.update_member(db, sid, me.id, name="x", craving=None)


async def test_begin_swiping_only_works_once(pg_sessions):
    sid = await make_session(pg_sessions)
    async with pg_sessions() as db:
        await svc.begin_swiping(db, sid)
    async with pg_sessions() as db:
        with pytest.raises(NotInLobby):
            await svc.begin_swiping(db, sid)


async def test_get_member_requires_the_right_session(pg_sessions):
    a, b = await make_session(pg_sessions), await make_session(pg_sessions)
    member = await join(pg_sessions, a)
    async with pg_sessions() as db:
        assert (await svc.get_member(db, a, member.id)).id == member.id
        with pytest.raises(NotAMember):
            await svc.get_member(db, b, member.id)
        with pytest.raises(NotAMember):
            await svc.get_member(db, a, "nope")


async def test_list_members_is_in_join_order(pg_sessions):
    sid = await make_session(pg_sessions)
    for name in ("Host", "B", "C"):
        await join(pg_sessions, sid, name=name, is_host=name == "Host")
    async with pg_sessions() as db:
        assert [m.name for m in await svc.list_members(db, sid)] == ["Host", "B", "C"]


async def test_save_votes_stores_votes_and_marks_submitted(pg_sessions):
    sid = await make_session(pg_sessions, phase="swiping")
    me = await join_in_lobby_then_start(pg_sessions, sid)
    async with pg_sessions() as db:
        await svc.save_votes(db, sid, me.id, {"p1": 1, "p2": -1, "p3": 2})
    async with pg_sessions() as db:
        rows = (await db.execute(select(VoteRecord).order_by(VoteRecord.place_id))).scalars().all()
        stored = await db.get(ParticipantRecord, me.id)
    assert [(v.place_id, v.value) for v in rows] == [("p1", 1), ("p2", -1), ("p3", 2)]
    assert stored.submitted_at is not None


async def join_in_lobby_then_start(sessions, sid):
    """Members can only join in the lobby, so add one directly for swiping-phase tests."""
    async with sessions() as db:
        member = ParticipantRecord(session_id=sid, name="Sam", is_host=False)
        db.add(member)
        await db.commit()
        return member


async def test_second_submit_is_rejected_and_adds_no_votes(pg_sessions):
    sid = await make_session(pg_sessions, phase="swiping")
    me = await join_in_lobby_then_start(pg_sessions, sid)
    async with pg_sessions() as db:
        await svc.save_votes(db, sid, me.id, {"p1": 1})
    async with pg_sessions() as db:
        with pytest.raises(AlreadySubmitted):
            await svc.save_votes(db, sid, me.id, {"p1": -1, "p2": 1})
    assert await count(pg_sessions, VoteRecord) == 1


async def test_concurrent_double_submit_stores_one_set_of_votes(pg_sessions):
    sid = await make_session(pg_sessions, phase="swiping")
    me = await join_in_lobby_then_start(pg_sessions, sid)

    async def submit():
        async with pg_sessions() as db:
            await svc.save_votes(db, sid, me.id, {"p1": 1, "p2": 1})

    results = await asyncio.gather(submit(), submit(), return_exceptions=True)
    assert sum(isinstance(r, AlreadySubmitted) for r in results) == 1
    assert await count(pg_sessions, VoteRecord) == 2


async def test_end_early_zero_fills_only_members_still_swiping(pg_sessions):
    sid = await make_session(pg_sessions, phase="swiping")
    done = await join_in_lobby_then_start(pg_sessions, sid)
    async with pg_sessions() as db:
        slow = ParticipantRecord(session_id=sid, name="Slow", is_host=False)
        db.add(slow)
        await db.commit()
    async with pg_sessions() as db:
        await svc.save_votes(db, sid, done.id, {"p1": 1, "p2": -1, "p3": 1})
    async with pg_sessions() as db:
        await svc.end_early(db, sid, PLACES)
        assert await svc.all_submitted(db, sid)
    async with pg_sessions() as db:
        votes = await svc.load_votes(db, sid)
    assert [v for v in votes if v[0] == "Slow"] == [("Slow", p, 0) for p in PLACES]
    assert [v[2] for v in votes if v[0] == "Sam"] == [1, -1, 1]  # not overwritten


async def test_all_submitted_is_false_while_someone_is_swiping(pg_sessions):
    sid = await make_session(pg_sessions, phase="swiping")
    await join_in_lobby_then_start(pg_sessions, sid)
    async with pg_sessions() as db:
        assert not await svc.all_submitted(db, sid)


async def test_finish_records_winner_and_phase(pg_sessions):
    sid = await make_session(pg_sessions, phase="swiping")
    async with pg_sessions() as db:
        await svc.finish(db, sid, "p2")
    async with pg_sessions() as db:
        record = await db.get(SessionRecord, sid)
    assert (record.phase, record.final_pick_place_id) == ("done", "p2")


async def test_deleting_a_session_cascades_to_members_and_votes(pg_sessions):
    sid = await make_session(pg_sessions, phase="swiping")
    me = await join_in_lobby_then_start(pg_sessions, sid)
    async with pg_sessions() as db:
        await svc.save_votes(db, sid, me.id, {"p1": 1})
    async with pg_sessions() as db:
        await db.delete(await db.get(SessionRecord, sid))
        await db.commit()
    assert await count(pg_sessions, ParticipantRecord) == 0
    assert await count(pg_sessions, VoteRecord) == 0


async def test_votes_and_ending_are_only_allowed_while_swiping(pg_sessions):
    sid = await make_session(pg_sessions)  # still in the lobby
    me = await join(pg_sessions, sid)
    async with pg_sessions() as db:
        with pytest.raises(NotSwiping):
            await svc.save_votes(db, sid, me.id, {"p1": 1})
    async with pg_sessions() as db:
        with pytest.raises(NotSwiping):
            await svc.end_early(db, sid, PLACES)
    assert await count(pg_sessions, VoteRecord) == 0


async def test_finish_twice_keeps_the_first_winner(pg_sessions):
    sid = await make_session(pg_sessions, phase="swiping")
    async with pg_sessions() as db:
        await svc.finish(db, sid, "p2")
    async with pg_sessions() as db:
        await svc.finish(db, sid, "p3")
        record = await db.get(SessionRecord, sid)
    assert record.final_pick_place_id == "p2"


async def test_create_group_session_makes_the_host_in_the_lobby(pg_sessions):
    payload = CreateSessionRequest(mode="group", initial_query=" tacos ", name="  ")
    async with pg_sessions() as db:
        sid, host_id = await svc.create_group_session(db, payload)
    async with pg_sessions() as db:
        record = await db.get(SessionRecord, sid)
        [host] = await svc.list_members(db, sid)
    assert (record.mode, record.phase) == ("group", "lobby")
    assert host.id == host_id and host.is_host and host.craving == "tacos"
    assert host.name.strip()  # a blank name was replaced by a generated one
