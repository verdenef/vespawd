"""Canonical project states."""

from __future__ import annotations

from enum import Enum


class ProjectState(str, Enum):
    CREATED = "created"
    INITIALIZED = "initialized"
    PLANNING = "planning"
    READY = "ready"
    EXECUTING = "executing"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    RECOVERING = "recovering"
    ARCHIVED = "archived"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def parse(cls, value: str) -> ProjectState | None:
        normalized = value.strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        return None

    @property
    def is_terminal(self) -> bool:
        return self in {ProjectState.COMPLETED, ProjectState.ARCHIVED}

    @property
    def allows_orchestration(self) -> bool:
        from vedaws.project.state.eligibility import allows_orchestration

        return allows_orchestration(self)

    @property
    def allows_dispatch(self) -> bool:
        from vedaws.project.state.eligibility import allows_dispatch

        return allows_dispatch(self)
