from api.utils.event_hub import CHANGED, CLOSED, EventHub
from api.utils.start_guard import StartGuard


async def test_notify_wakes_every_stream_of_that_session_only():
    hub = EventHub()
    a, b = hub.subscribe("s1", "p1"), hub.subscribe("s1", "p2")
    other = hub.subscribe("s2", "p3")
    hub.notify("s1")
    assert a.get_nowait() is CHANGED and b.get_nowait() is CHANGED
    assert other.empty()


async def test_repeated_notifies_merge_into_one_wakeup():
    hub = EventHub()
    queue = hub.subscribe("s1", "p1")
    for _ in range(5):
        hub.notify("s1")
    assert queue.qsize() == 1


async def test_a_new_stream_for_the_same_member_closes_the_old_one():
    hub = EventHub()
    old = hub.subscribe("s1", "p1")
    new = hub.subscribe("s1", "p1")
    assert old.get_nowait() is CLOSED
    hub.notify("s1")
    assert new.get_nowait() is CHANGED and old.empty()


async def test_unsubscribe_only_removes_its_own_stream():
    hub = EventHub()
    old = hub.subscribe("s1", "p1")
    new = hub.subscribe("s1", "p1")
    hub.unsubscribe("s1", "p1", old)  # the old stream ending must not drop the new one
    hub.notify("s1")
    assert new.get_nowait() is CHANGED
    hub.unsubscribe("s1", "p1", new)
    hub.notify("s1")  # nobody left: no error


def test_start_guard_allows_one_start_at_a_time():
    guard = StartGuard()
    assert guard.try_acquire("s1")
    assert not guard.try_acquire("s1") and guard.is_active("s1")
    assert guard.try_acquire("s2")
    guard.release("s1")
    assert not guard.is_active("s1") and guard.try_acquire("s1")
