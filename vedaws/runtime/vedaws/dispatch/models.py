"""Dispatch result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DispatchStatus(str, Enum):
    DISPATCHED = "dispatched"
    NO_WORKER = "no_worker"
    NO_TASK = "no_task"
    INCOMPATIBLE = "incompatible"
    ERROR = "error"
    SKIPPED = "skipped"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class DispatchResult:
    status: DispatchStatus
    workflow_id: str = ""
    task_id: str = ""
    worker_id: str = ""
    message: str = ""
    success: bool | None = None

    @property
    def task_key(self) -> str:
        if self.workflow_id and self.task_id:
            return f"{self.workflow_id}.{self.task_id}"
        return ""


@dataclass
class RunSummary:
    dispatched: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    blocked: bool = False
    cancelled: bool = False
    cycles: int = 0
    retries: int = 0
    blocking_reason: str = ""
    blocked_tasks: list[str] = field(default_factory=list)
    results: list[DispatchResult] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        return self.dispatched
