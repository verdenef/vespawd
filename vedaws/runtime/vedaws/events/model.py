"""Canonical event model."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping


def _freeze_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    return dict(value)


@dataclass(frozen=True)
class Event:
    """Immutable published event."""

    id: str
    type: str
    timestamp: datetime
    source: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", MappingProxyType(_freeze_mapping(self.payload)))
        object.__setattr__(self, "metadata", MappingProxyType(_freeze_mapping(self.metadata)))


def create_event(
    event_type: str,
    *,
    source: str,
    payload: Mapping[str, Any] | None = None,
    correlation_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
    event_id: str | None = None,
    timestamp: datetime | None = None,
) -> Event:
    return Event(
        id=event_id or str(uuid.uuid4()),
        type=event_type,
        timestamp=timestamp or datetime.now(timezone.utc),
        source=source,
        payload=payload or {},
        correlation_id=correlation_id,
        metadata=metadata or {},
    )
