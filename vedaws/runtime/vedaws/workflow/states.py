"""Workflow and task lifecycle states."""

from __future__ import annotations

from enum import Enum


class WorkflowStatus(str, Enum):
    DEFINED = "defined"
    ACTIVATED = "activated"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def parse(cls, value: str) -> WorkflowStatus | None:
        normalized = value.strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        return None


class TaskStatus(str, Enum):
    DEFINED = "defined"
    PENDING = "pending"
    READY = "ready"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RECORDED = "recorded"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def parse(cls, value: str) -> TaskStatus | None:
        normalized = value.strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        return None

    @property
    def is_terminal(self) -> bool:
        return self in {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.RECORDED,
        }
