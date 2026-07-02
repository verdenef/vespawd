"""Workflow progress tracking and status derivation."""

from __future__ import annotations

from dataclasses import dataclass

from vedaws.workflow.models import TaskInstance, WorkflowDefinition, WorkflowInstance
from vedaws.workflow.registry import TaskRegistry
from vedaws.workflow.states import TaskStatus, WorkflowStatus

ACTIVE_TASK_STATUSES = frozenset({
    TaskStatus.PENDING,
    TaskStatus.READY,
    TaskStatus.DISPATCHED,
    TaskStatus.RUNNING,
})


@dataclass(frozen=True)
class WorkflowProgress:
    workflow_id: str
    status: WorkflowStatus
    total_tasks: int
    completed: int
    failed: int
    ready: int
    pending: int
    in_flight: int

    @property
    def percent_complete(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return round((self.completed / self.total_tasks) * 100, 1)


def derive_workflow_status(
    workflow: WorkflowDefinition,
    instance: WorkflowInstance,
    registry: TaskRegistry,
) -> WorkflowStatus:
    if instance.status == WorkflowStatus.CANCELLED:
        return WorkflowStatus.CANCELLED
    if instance.status == WorkflowStatus.DEFINED:
        return WorkflowStatus.DEFINED

    tasks = registry.list_for_workflow(workflow.id)
    if not tasks:
        return instance.status

    statuses = [task.status for task in tasks]
    if any(status == TaskStatus.FAILED for status in statuses):
        return WorkflowStatus.BLOCKED
    if all(status in {TaskStatus.COMPLETED, TaskStatus.RECORDED} for status in statuses):
        return WorkflowStatus.COMPLETED
    if any(status in ACTIVE_TASK_STATUSES for status in statuses):
        return WorkflowStatus.IN_PROGRESS
    if instance.status == WorkflowStatus.ACTIVATED:
        return WorkflowStatus.ACTIVATED
    return instance.status


def compute_progress(
    workflow: WorkflowDefinition,
    instance: WorkflowInstance,
    registry: TaskRegistry,
) -> WorkflowProgress:
    tasks = registry.list_for_workflow(workflow.id)
    status = derive_workflow_status(workflow, instance, registry)
    return WorkflowProgress(
        workflow_id=workflow.id,
        status=status,
        total_tasks=len(workflow.tasks),
        completed=sum(1 for task in tasks if task.status in {TaskStatus.COMPLETED, TaskStatus.RECORDED}),
        failed=sum(1 for task in tasks if task.status == TaskStatus.FAILED),
        ready=sum(1 for task in tasks if task.status == TaskStatus.READY),
        pending=sum(1 for task in tasks if task.status == TaskStatus.PENDING),
        in_flight=sum(
            1 for task in tasks if task.status in {TaskStatus.DISPATCHED, TaskStatus.RUNNING}
        ),
    )


def dependencies_satisfied(
    workflow_id: str,
    task_def: TaskDefinition,
    registry: TaskRegistry,
) -> bool:
    for dep_id in task_def.depends_on:
        dep = registry.get_instance(workflow_id, dep_id)
        if dep is None:
            return False
        if dep.status not in {TaskStatus.COMPLETED, TaskStatus.RECORDED}:
            return False
    return True


def evaluate_task_readiness(
    workflow: WorkflowDefinition,
    registry: TaskRegistry,
) -> list[TaskInstance]:
    updated: list[TaskInstance] = []
    for task_def in workflow.tasks:
        instance = registry.ensure_instance(workflow.id, task_def.id)
        if instance.status.is_terminal or instance.status in {
            TaskStatus.DISPATCHED,
            TaskStatus.RUNNING,
        }:
            continue
        if instance.status == TaskStatus.DEFINED:
            continue
        if dependencies_satisfied(workflow.id, task_def, registry):
            if instance.status == TaskStatus.PENDING:
                instance.status = TaskStatus.READY
                updated.append(instance)
        elif instance.status == TaskStatus.READY:
            instance.status = TaskStatus.PENDING
            updated.append(instance)
    return updated
