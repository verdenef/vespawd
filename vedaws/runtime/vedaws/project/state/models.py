"""State transition models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from vedaws.project.state.states import ProjectState
from vedaws.project.state.triggers import TransitionTrigger


@dataclass(frozen=True)
class TransitionRecord:
    timestamp: str
    previous_state: str
    new_state: str
    trigger: str
    reason: str | None = None

    @classmethod
    def create(
        cls,
        previous: ProjectState,
        new: ProjectState,
        trigger: TransitionTrigger,
        reason: str | None = None,
        *,
        timestamp: datetime | None = None,
    ) -> TransitionRecord:
        moment = timestamp or datetime.now(timezone.utc)
        return cls(
            timestamp=moment.isoformat(),
            previous_state=previous.value,
            new_state=new.value,
            trigger=trigger.value,
            reason=reason,
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if data["reason"] is None:
            del data["reason"]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransitionRecord:
        return cls(
            timestamp=str(data["timestamp"]),
            previous_state=str(data["previous_state"]),
            new_state=str(data["new_state"]),
            trigger=str(data["trigger"]),
            reason=data.get("reason"),
        )


class InvalidTransitionError(ValueError):
    """Raised when a state transition is not permitted."""


class StateValidationError(ValueError):
    """Raised when persisted project state is invalid."""
