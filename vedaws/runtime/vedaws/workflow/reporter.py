"""CLI formatting for workflows and tasks."""

from __future__ import annotations

from vedaws.workflow.engine import WorkflowEngine
from vedaws.workflow.models import WorkflowDefinition
from vedaws.workflow.states import TaskStatus


def format_workflow_list(engine: WorkflowEngine, project_name: str) -> str:
    lines = [f"Workflows for project '{project_name}':", ""]
    workflows = engine.list_workflows()
    if not workflows:
        lines.append("  (no workflow definitions — add *.workflow.toml under .vedaws/workflows/)")
        return "\n".join(lines)

    for workflow in workflows:
        progress = engine.progress(workflow.id)
        lines.append(
            f"  {workflow.id} — {workflow.name} [{progress.status.value}] "
            f"({progress.completed}/{progress.total_tasks} tasks, {progress.percent_complete}%)"
        )
    invalid = engine.load_result.invalid
    if invalid:
        lines.extend(["", f"Invalid manifests: {len(invalid)}"])
    return "\n".join(lines)


def format_workflow_detail(engine: WorkflowEngine, workflow_id: str) -> str:
    workflow = engine.get_workflow(workflow_id)
    if workflow is None:
        return f"Workflow '{workflow_id}' not found."

    instance = engine.get_workflow_instance(workflow_id)
    progress = engine.progress(workflow_id)
    lines = [
        f"Workflow: {workflow.name} ({workflow.id})",
        f"Version:  {workflow.version}",
        f"Status:   {progress.status.value}",
        f"Progress: {progress.completed}/{progress.total_tasks} completed "
        f"({progress.percent_complete}%)",
    ]
    if workflow.description:
        lines.append(f"About:    {workflow.description}")
    if instance and instance.activated_at:
        lines.append(f"Activated: {instance.activated_at}")

    lines.extend(["", "Tasks:"])
    for task_def in workflow.tasks:
        task = engine.task_registry.get_instance(workflow.id, task_def.id)
        status = task.status.value if task else TaskStatus.DEFINED.value
        deps = ", ".join(task_def.depends_on) if task_def.depends_on else "(none)"
        cap = task_def.capability or "(any)"
        lines.append(f"  {workflow.id}.{task_def.id} [{status}] — {task_def.name}")
        lines.append(f"    depends_on: {deps}  capability: {cap}")
    return "\n".join(lines)


def format_task_list(engine: WorkflowEngine, project_name: str) -> str:
    lines = [f"Tasks for project '{project_name}':", ""]
    tasks = engine.task_registry.list_all()
    if not tasks:
        lines.append("  (no tasks — activate a workflow first)")
        return "\n".join(lines)

    for task in tasks:
        definition = engine.task_registry.get_definition(task.workflow_id, task.task_id)
        name = definition.name if definition else task.task_id
        lines.append(f"  {task.key} [{task.status.value}] — {name}")
    return "\n".join(lines)


def format_task_detail(engine: WorkflowEngine, workflow_id: str, task_id: str) -> str:
    definition = engine.task_registry.get_definition(workflow_id, task_id)
    instance = engine.task_registry.get_instance(workflow_id, task_id)
    if definition is None:
        return f"Task '{workflow_id}.{task_id}' not found."

    status = instance.status.value if instance else TaskStatus.DEFINED.value
    lines = [
        f"Task: {definition.name} ({workflow_id}.{task_id})",
        f"Status: {status}",
    ]
    if definition.description:
        lines.append(f"Description: {definition.description}")
    if definition.depends_on:
        lines.append(f"Depends on: {', '.join(definition.depends_on)}")
    if definition.capability:
        lines.append(f"Capability: {definition.capability}")
    if instance and instance.assigned_worker_id:
        lines.append(f"Worker: {instance.assigned_worker_id}")
    if instance and instance.outcome_message:
        lines.append(f"Outcome: {instance.outcome_message}")
    if definition.requires_approval:
        lines.append("Requires approval: yes")
    return "\n".join(lines)
