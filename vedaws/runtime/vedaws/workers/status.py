"""Worker lifecycle and health status."""

from __future__ import annotations

from enum import Enum


class WorkerStatus(str, Enum):
    REGISTERED = "registered"
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    EXECUTING = "executing"
    UNAVAILABLE = "unavailable"
    INVALID = "invalid"
    RETIRED = "retired"

    def __str__(self) -> str:
        return self.value


class WorkerHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value
