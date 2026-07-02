"""In-process Event Bus — synchronous publish/subscribe."""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from vedaws.events.model import Event
from vedaws.events.types import SYSTEM_EVENT_TYPES

logger = logging.getLogger("vedaws.events")

EventHandler = Callable[[Event], None]


@dataclass(frozen=True)
class Subscription:
    subscription_id: str
    event_type: str
    subscriber_id: str
    handler: EventHandler
    source: str = ""


@dataclass
class EventBusStats:
    total_published: int = 0
    published_by_type: dict[str, int] = field(default_factory=dict)
    subscriber_count: int = 0
    subscribers_by_type: dict[str, int] = field(default_factory=dict)
    known_event_types: tuple[str, ...] = SYSTEM_EVENT_TYPES
    duplicate_replacements: int = 0


class EventBus:
    """Runtime-owned synchronous event bus."""

    def __init__(self) -> None:
        self._subscriptions: dict[str, list[Subscription]] = defaultdict(list)
        self._subscription_index: dict[str, Subscription] = {}
        self._published_counts: dict[str, int] = defaultdict(int)
        self._total_published = 0
        self._duplicate_replacements = 0
        self._observed_types: set[str] = set(SYSTEM_EVENT_TYPES)

    def publish(self, event: Event) -> None:
        """Publish an event and dispatch synchronously to subscribers."""
        self._observed_types.add(event.type)
        self._total_published += 1
        self._published_counts[event.type] += 1
        logger.debug("Publishing event %s (%s) from %s", event.id, event.type, event.source)

        for subscription in list(self._subscriptions.get(event.type, [])):
            try:
                subscription.handler(event)
            except Exception:  # noqa: BLE001
                logger.exception(
                    "Event handler failed for %s (subscriber=%s)",
                    event.type,
                    subscription.subscriber_id,
                )

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
        *,
        subscriber_id: str,
        source: str = "",
        subscription_id: str | None = None,
    ) -> str:
        """Subscribe to an event type. Duplicate subscriber_id replaces prior subscription."""
        sub_id = subscription_id or f"{subscriber_id}:{event_type}"
        existing = self._subscription_index.get(sub_id)
        if existing is not None:
            self._remove_subscription(existing)
            self._duplicate_replacements += 1

        subscription = Subscription(
            subscription_id=sub_id,
            event_type=event_type,
            subscriber_id=subscriber_id,
            handler=handler,
            source=source,
        )
        self._subscriptions[event_type].append(subscription)
        self._subscription_index[sub_id] = subscription
        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        subscription = self._subscription_index.pop(subscription_id, None)
        if subscription is None:
            return False
        self._remove_subscription(subscription)
        return True

    def unsubscribe_subscriber(self, subscriber_id: str) -> int:
        removed = 0
        for sub_id, subscription in list(self._subscription_index.items()):
            if subscription.subscriber_id == subscriber_id:
                if self.unsubscribe(sub_id):
                    removed += 1
        return removed

    def list_event_types(self) -> list[str]:
        types = set(SYSTEM_EVENT_TYPES)
        types.update(self._observed_types)
        types.update(self._subscriptions.keys())
        types.update(self._published_counts.keys())
        return sorted(types)

    def stats(self) -> EventBusStats:
        subscribers_by_type = {
            event_type: len(subs) for event_type, subs in self._subscriptions.items() if subs
        }
        return EventBusStats(
            total_published=self._total_published,
            published_by_type=dict(self._published_counts),
            subscriber_count=len(self._subscription_index),
            subscribers_by_type=subscribers_by_type,
            known_event_types=tuple(self.list_event_types()),
            duplicate_replacements=self._duplicate_replacements,
        )

    def _remove_subscription(self, subscription: Subscription) -> None:
        handlers = self._subscriptions.get(subscription.event_type, [])
        self._subscriptions[subscription.event_type] = [
            item for item in handlers if item.subscription_id != subscription.subscription_id
        ]
