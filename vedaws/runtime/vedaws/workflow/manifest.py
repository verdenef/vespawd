"""Workflow definition manifest parsing."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from vedaws.workflow.models import TaskDefinition, WorkflowDefinition

WORKFLOW_MANIFEST_SUFFIX = ".workflow.toml"


def parse_workflow_manifest(path: Path) -> tuple[WorkflowDefinition | None, str | None]:
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except OSError as exc:
        return None, f"cannot read manifest: {exc}"
    except tomllib.TOMLDecodeError as exc:
        return None, f"invalid TOML: {exc}"

    workflow = data.get("workflow", data)
    workflow_id = str(workflow.get("id", "")).strip()
    if not workflow_id:
        return None, "missing workflow id"

    raw_tasks = data.get("tasks", [])
    tasks = _parse_tasks(raw_tasks)
    if not tasks:
        return None, "at least one task is required"

    return WorkflowDefinition(
        id=workflow_id,
        name=str(workflow.get("name", workflow_id)),
        version=str(workflow.get("version", "0.1.0")),
        description=str(workflow.get("description", "")),
        tasks=tuple(tasks),
    ), None


def _parse_tasks(raw: Any) -> list[TaskDefinition]:
    if not isinstance(raw, list):
        return []

    tasks: list[TaskDefinition] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        task_id = str(entry.get("id", "")).strip()
        if not task_id:
            continue
        depends = entry.get("depends_on", [])
        if isinstance(depends, str):
            depends = [depends]
        raw_skills = entry.get("skills", [])
        if isinstance(raw_skills, str):
            raw_skills = [raw_skills]
        elif not isinstance(raw_skills, list):
            raw_skills = []
        if not raw_skills and isinstance(entry.get("skill"), str):
            raw_skills = [entry["skill"]]
        tasks.append(
            TaskDefinition(
                id=task_id,
                name=str(entry.get("name", task_id)),
                description=str(entry.get("description", "")),
                depends_on=tuple(str(dep) for dep in depends if str(dep).strip()),
                capability=str(entry.get("capability", "")),
                ai_capability=str(entry.get("ai_capability", "")),
                skills=tuple(str(skill) for skill in raw_skills if str(skill).strip()),
                requires_approval=bool(entry.get("requires_approval", False)),
            )
        )
    return tasks
