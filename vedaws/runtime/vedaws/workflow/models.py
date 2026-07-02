"""Workflow and task models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from vedaws.workflow.states import TaskStatus, WorkflowStatus


@dataclass(frozen=True)
class TaskDefinition:
    id: str
    name: str
    description: str = ""
    depends_on: tuple[str, ...] = ()
    capability: str = ""
    ai_capability: str = ""
    skills: tuple[str, ...] = ()
    requires_approval: bool = False

    @property
    def key(self) -> str:
        return self.id


@dataclass(frozen=True)
class WorkflowDefinition:
    id: str
    name: str
    version: str = "0.1.0"
    description: str = ""
    tasks: tuple[TaskDefinition, ...] = ()

    def get_task(self, task_id: str) -> TaskDefinition | None:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None


@dataclass
class TaskInstance:
    workflow_id: str
    task_id: str
    status: TaskStatus = TaskStatus.DEFINED
    assigned_worker_id: str | None = None
    outcome_message: str | None = None
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def key(self) -> str:
        return f"{self.workflow_id}.{self.task_id}"


@dataclass
class WorkflowInstance:
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.DEFINED
    activated_at: str | None = None
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
