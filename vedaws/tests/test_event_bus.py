"""Event bus unit tests."""

from __future__ import annotations

import pytest

from vedaws.events.bus import EventBus
from vedaws.events.model import Event, create_event
from vedaws.events.types import EventType


def test_event_is_immutable() -> None:
    event = create_event(EventType.PROJECT_INITIALIZED, source="test", payload={"a": 1})
    with pytest.raises(TypeError):
        event.payload["a"] = 2  # type: ignore[index]


def test_publish_dispatches_synchronously() -> None:
    bus = EventBus()
    received: list[Event] = []

    bus.subscribe(
        EventType.TASK_COMPLETED,
        received.append,
        subscriber_id="test-subscriber",
    )
    event = create_event(EventType.TASK_COMPLETED, source="test", payload={"task_id": "t1"})
    bus.publish(event)

    assert len(received) == 1
    assert received[0].id == event.id
    assert bus.stats().total_published == 1


def test_unsubscribe_removes_handler() -> None:
    bus = EventBus()
    received: list[Event] = []

    sub_id = bus.subscribe(
        EventType.WORKER_STARTED,
        received.append,
        subscriber_id="worker-observer",
    )
    bus.unsubscribe(sub_id)
    bus.publish(create_event(EventType.WORKER_STARTED, source="test"))

    assert received == []


def test_duplicate_subscription_replaces_prior() -> None:
    bus = EventBus()
    first: list[Event] = []
    second: list[Event] = []

    bus.subscribe(
        EventType.PLUGIN_LOADED,
        first.append,
        subscriber_id="plugin:hello:observer",
    )
    bus.subscribe(
        EventType.PLUGIN_LOADED,
        second.append,
        subscriber_id="plugin:hello:observer",
    )
    bus.publish(create_event(EventType.PLUGIN_LOADED, source="test"))

    assert first == []
    assert len(second) == 1
    assert bus.stats().duplicate_replacements == 1


def test_stats_track_types_and_subscribers() -> None:
    bus = EventBus()
    bus.subscribe(EventType.TASK_FAILED, lambda _e: None, subscriber_id="a")
    bus.subscribe(EventType.TASK_FAILED, lambda _e: None, subscriber_id="b")
    bus.publish(create_event(EventType.TASK_FAILED, source="test"))
    bus.publish(create_event("CustomEvent", source="test"))

    stats = bus.stats()
    assert stats.subscriber_count == 2
    assert stats.published_by_type[EventType.TASK_FAILED] == 1
    assert stats.published_by_type["CustomEvent"] == 1
    assert "CustomEvent" in stats.known_event_types
