"""Task dispatch and outcome models for worker execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from vedaws.workflow.models import TaskDefinition


class TaskOutcomeStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    ESCALATION = "escalation"

    def __str__(self) -> str:
        return self.value

    @property
    def is_success(self) -> bool:
        return self == TaskOutcomeStatus.SUCCESS


@dataclass(frozen=True)
class TaskDispatch:
    """Package sent to a worker for execution."""

    workflow_id: str
    task_id: str
    task: TaskDefinition
    project_name: str = ""
    instructions: str = ""

    @property
    def key(self) -> str:
        return f"{self.workflow_id}.{self.task_id}"


@dataclass(frozen=True)
class TaskOutcome:
    """Result returned by a worker after execution."""

    status: TaskOutcomeStatus
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, message: str = "", **data: Any) -> TaskOutcome:
        return cls(status=TaskOutcomeStatus.SUCCESS, message=message, data=dict(data))

    @classmethod
    def failure(cls, message: str = "", **data: Any) -> TaskOutcome:
        return cls(status=TaskOutcomeStatus.FAILURE, message=message, data=dict(data))
