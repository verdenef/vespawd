"""Event bus status reporting for CLI."""

from __future__ import annotations

from vedaws.events.bus import EventBus


def format_event_bus_status(event_bus: EventBus) -> str:
    stats = event_bus.stats()
    lines = [
        "Event Bus:",
        "",
        f"  Total published:     {stats.total_published}",
        f"  Subscriber count:    {stats.subscriber_count}",
        f"  Duplicate replaced:  {stats.duplicate_replacements}",
        "",
        "Registered event types:",
    ]

    if not stats.known_event_types:
        lines.append("  (none)")
    else:
        for event_type in stats.known_event_types:
            published = stats.published_by_type.get(event_type, 0)
            subscribers = stats.subscribers_by_type.get(event_type, 0)
            lines.append(
                f"  - {event_type:<22} published={published:<4} subscribers={subscribers}"
            )

    if stats.published_by_type:
        extra_types = sorted(
            set(stats.published_by_type) - set(stats.known_event_types)
        )
        for event_type in extra_types:
            published = stats.published_by_type[event_type]
            subscribers = stats.subscribers_by_type.get(event_type, 0)
            lines.append(
                f"  - {event_type:<22} published={published:<4} subscribers={subscribers} (custom)"
            )

    return "\n".join(lines)
