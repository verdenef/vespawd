"""Persist workflow and task progress."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vedaws.workflow.models import TaskInstance, WorkflowInstance
from vedaws.workflow.states import TaskStatus, WorkflowStatus

PROGRESS_FILE_NAME = "workflow-progress.json"


def progress_file_path(project_dir: Path) -> Path:
    return project_dir / PROGRESS_FILE_NAME


def load_progress(project_dir: Path) -> tuple[dict[str, WorkflowInstance], dict[str, TaskInstance]]:
    path = progress_file_path(project_dir)
    if not path.is_file():
        return {}, {}

    data = json.loads(path.read_text(encoding="utf-8"))
    workflows = {
        key: _workflow_from_dict(value)
        for key, value in data.get("workflows", {}).items()
    }
    tasks = {
        key: _task_from_dict(key, value)
        for key, value in data.get("tasks", {}).items()
    }
    return workflows, tasks


def save_progress(
    project_dir: Path,
    workflows: dict[str, WorkflowInstance],
    tasks: dict[str, TaskInstance],
) -> None:
    project_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "workflows": {key: _workflow_to_dict(value) for key, value in workflows.items()},
        "tasks": {key: _task_to_dict(value) for key, value in tasks.items()},
    }
    progress_file_path(project_dir).write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def _workflow_to_dict(instance: WorkflowInstance) -> dict[str, Any]:
    return {
        "workflow_id": instance.workflow_id,
        "status": instance.status.value,
        "activated_at": instance.activated_at,
        "updated_at": instance.updated_at,
    }


def _workflow_from_dict(data: dict[str, Any]) -> WorkflowInstance:
    status = WorkflowStatus.parse(str(data.get("status", "defined"))) or WorkflowStatus.DEFINED
    return WorkflowInstance(
        workflow_id=str(data.get("workflow_id", "")),
        status=status,
        activated_at=data.get("activated_at"),
        updated_at=str(data.get("updated_at", "")),
    )


def _task_to_dict(instance: TaskInstance) -> dict[str, Any]:
    return {
        "workflow_id": instance.workflow_id,
        "task_id": instance.task_id,
        "status": instance.status.value,
        "assigned_worker_id": instance.assigned_worker_id,
        "outcome_message": instance.outcome_message,
        "updated_at": instance.updated_at,
    }


def _task_from_dict(key: str, data: dict[str, Any]) -> TaskInstance:
    workflow_id = str(data.get("workflow_id", ""))
    task_id = str(data.get("task_id", ""))
    if not workflow_id or not task_id:
        parts = key.split(".", 1)
        workflow_id = workflow_id or (parts[0] if parts else "")
        task_id = task_id or (parts[1] if len(parts) > 1 else key)
    status = TaskStatus.parse(str(data.get("status", "defined"))) or TaskStatus.DEFINED
    return TaskInstance(
        workflow_id=workflow_id,
        task_id=task_id,
        status=status,
        assigned_worker_id=data.get("assigned_worker_id"),
        outcome_message=data.get("outcome_message"),
        updated_at=str(data.get("updated_at", "")),
    )
