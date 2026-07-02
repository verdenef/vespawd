"""Runtime lifecycle status."""

from __future__ import annotations

from enum import Enum


class RuntimeStatus(str, Enum):
    INACTIVE = "inactive"
    STARTING = "starting"
    ACTIVE = "active"
    STOPPING = "stopping"

    def __str__(self) -> str:
        return self.value
