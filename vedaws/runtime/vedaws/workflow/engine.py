"""Workflow engine — load, activate, track, and sync project state."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from vedaws.config.paths import PROJECT_WORKFLOWS_DIR
from vedaws.events.bus import EventBus
from vedaws.events.model import create_event
from vedaws.events.types import EventType
from vedaws.project.state.bridge import apply_state_transition
from vedaws.project.state.engine import StateEngine
from vedaws.project.state.states import ProjectState
from vedaws.project.state.triggers import TransitionTrigger
from vedaws.workflow.loader import WorkflowLoadResult, load_workflow_definitions
from vedaws.workflow.models import TaskInstance, WorkflowDefinition, WorkflowInstance
from vedaws.workflow.persistence import load_progress, save_progress
from vedaws.workflow.registry import TaskRegistry
from vedaws.workflow.states import TaskStatus, WorkflowStatus
from vedaws.workflow.tracker import (
    compute_progress,
    derive_workflow_status,
    evaluate_task_readiness,
)

logger = logging.getLogger("vedaws.workflow")

WORKFLOWS_DIR_NAME = PROJECT_WORKFLOWS_DIR


class WorkflowError(Exception):
    """Base workflow engine error."""


class WorkflowNotFoundError(WorkflowError):
    pass


class TaskNotFoundError(WorkflowError):
    pass


class InvalidTaskTransitionError(WorkflowError):
    pass


class WorkflowEngine:
    """Models workflow definitions, task lifecycle, and progress within a project."""

    def __init__(
        self,
        project_dir: Path,
        workflows: dict[str, WorkflowDefinition],
        workflow_instances: dict[str, WorkflowInstance],
        task_registry: TaskRegistry,
        state_engine: StateEngine | None = None,
        load_result: WorkflowLoadResult | None = None,
    ) -> None:
        self._project_dir = project_dir
        self._workflows = workflows
        self._workflow_instances = workflow_instances
        self._tasks = task_registry
        self._state_engine = state_engine
        self._load_result = load_result or WorkflowLoadResult()
        self._event_bus: EventBus | None = None

    @classmethod
    def load(
        cls,
        project_dir: Path,
        *,
        state_engine: StateEngine | None = None,
    ) -> WorkflowEngine:
        workflows_dir = project_dir / WORKFLOWS_DIR_NAME
        load_result = load_workflow_definitions(workflows_dir)
        workflow_map = {workflow.id: workflow for workflow in load_result.workflows}

        registry = TaskRegistry()
        for workflow in workflow_map.values():
            registry.register_workflow(workflow)

        wf_instances, task_instances = load_progress(project_dir)
        registry.instances.update(task_instances)

        for workflow in workflow_map.values():
            if workflow.id not in wf_instances:
                wf_instances[workflow.id] = WorkflowInstance(workflow_id=workflow.id)
            for task_def in workflow.tasks:
                registry.ensure_instance(workflow.id, task_def.id)

        engine = cls(
            project_dir,
            workflow_map,
            wf_instances,
            registry,
            state_engine=state_engine,
            load_result=load_result,
        )
        engine._refresh_all_workflows(persist=False, sync_state=False)
        return engine

    @property
    def project_dir(self) -> Path:
        return self._project_dir

    @property
    def workflows_dir(self) -> Path:
        return self._project_dir / WORKFLOWS_DIR_NAME

    @property
    def load_result(self) -> WorkflowLoadResult:
        return self._load_result

    @property
    def task_registry(self) -> TaskRegistry:
        return self._tasks

    @property
    def state_engine(self) -> StateEngine | None:
        return self._state_engine

    def attach_event_bus(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus

    def list_workflows(self) -> list[WorkflowDefinition]:
        return sorted(self._workflows.values(), key=lambda workflow: workflow.id)

    def get_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        return self._workflows.get(workflow_id)

    def get_workflow_instance(self, workflow_id: str) -> WorkflowInstance | None:
        return self._workflow_instances.get(workflow_id)

    def progress(self, workflow_id: str):
        workflow = self._require_workflow(workflow_id)
        instance = self._require_workflow_instance(workflow_id)
        return compute_progress(workflow, instance, self._tasks)

    def activate(self, workflow_id: str) -> WorkflowInstance:
        workflow = self._require_workflow(workflow_id)
        instance = self._require_workflow_instance(workflow_id)
        if instance.status not in {WorkflowStatus.DEFINED, WorkflowStatus.CANCELLED}:
            raise WorkflowError(
                f"Workflow '{workflow_id}' cannot be activated from status {instance.status.value}"
            )

        now = _now_iso()
        instance.status = WorkflowStatus.ACTIVATED
        instance.activated_at = now
        instance.updated_at = now

        for task_def in workflow.tasks:
            task = self._tasks.ensure_instance(workflow.id, task_def.id)
            task.status = TaskStatus.PENDING
            task.updated_at = now
            self._publish_event(
                EventType.TASK_CREATED,
                {
                    "workflow_id": workflow.id,
                    "task_id": task_def.id,
                    "capability": task_def.capability,
                },
            )

        self._publish_event(
            EventType.WORKFLOW_STARTED,
            {"workflow_id": workflow_id, "task_count": len(workflow.tasks)},
        )

        self._try_state_transition(
            ProjectState.PLANNING,
            f"Workflow '{workflow_id}' activated",
        )
        self._refresh_workflow(workflow_id)
        self._sync_project_state(f"Workflow '{workflow_id}' activated")
        self._persist()
        return instance

    def complete_task(self, workflow_id: str, task_id: str) -> TaskInstance:
        """Record a successful outcome without worker execution (testing / recovery)."""
        return self._apply_task_outcome(workflow_id, task_id, success=True)

    def fail_task(self, workflow_id: str, task_id: str) -> TaskInstance:
        """Record a failed outcome without worker execution (testing / recovery)."""
        return self._apply_task_outcome(workflow_id, task_id, success=False)

    def mark_dispatched(
        self, workflow_id: str, task_id: str, worker_id: str
    ) -> TaskInstance:
        instance = self._require_runnable_task(workflow_id, task_id, TaskStatus.READY)
        now = _now_iso()
        instance.status = TaskStatus.DISPATCHED
        instance.assigned_worker_id = worker_id
        instance.updated_at = now
        self._persist()
        return instance

    def mark_running(self, workflow_id: str, task_id: str) -> TaskInstance:
        instance = self._require_runnable_task(workflow_id, task_id, TaskStatus.DISPATCHED)
        instance.status = TaskStatus.RUNNING
        instance.updated_at = _now_iso()
        self._publish_event(
            EventType.TASK_STARTED,
            {
                "workflow_id": workflow_id,
                "task_id": task_id,
                "worker_id": instance.assigned_worker_id or "",
            },
        )
        self._persist()
        return instance

    def record_worker_outcome(
        self,
        workflow_id: str,
        task_id: str,
        *,
        success: bool,
        message: str | None = None,
    ) -> TaskInstance:
        return self._apply_task_outcome(
            workflow_id,
            task_id,
            success=success,
            message=message,
            from_status=TaskStatus.RUNNING,
        )

    def ensure_executing(self, reason: str) -> None:
        """Transition project to executing when work is in flight."""
        self._try_state_transition(ProjectState.EXECUTING, reason)

    def sync_project_state(self, reason: str) -> None:
        """Reconcile project state from current workflow progress."""
        self._sync_project_state(reason)

    def _require_runnable_task(
        self, workflow_id: str, task_id: str, expected: TaskStatus
    ) -> TaskInstance:
        task_def = self._tasks.get_definition(workflow_id, task_id)
        if task_def is None:
            raise TaskNotFoundError(f"Task '{workflow_id}.{task_id}' not found")
        instance = self._tasks.ensure_instance(workflow_id, task_id)
        if instance.status != expected:
            raise InvalidTaskTransitionError(
                f"Task '{workflow_id}.{task_id}' expected {expected.value}, "
                f"got {instance.status.value}"
            )
        return instance

    def _apply_task_outcome(
        self,
        workflow_id: str,
        task_id: str,
        *,
        success: bool,
        message: str | None = None,
        from_status: TaskStatus = TaskStatus.READY,
    ) -> TaskInstance:
        workflow = self._require_workflow(workflow_id)
        task_def = self._tasks.get_definition(workflow_id, task_id)
        if task_def is None:
            raise TaskNotFoundError(f"Task '{workflow_id}.{task_id}' not found")

        instance = self._tasks.ensure_instance(workflow_id, task_id)
        if instance.status != from_status:
            if instance.status.is_terminal:
                raise InvalidTaskTransitionError(
                    f"Task '{workflow_id}.{task_id}' is already terminal ({instance.status.value})"
                )
            raise InvalidTaskTransitionError(
                f"Task '{workflow_id}.{task_id}' must be {from_status.value} before recording "
                f"outcome (current: {instance.status.value})"
            )

        now = _now_iso()
        if success:
            instance.status = TaskStatus.COMPLETED
            instance.outcome_message = message
            instance.updated_at = now
            self._publish_event(
                EventType.TASK_COMPLETED,
                {
                    "workflow_id": workflow_id,
                    "task_id": task_id,
                    "message": message or "",
                },
            )
            self._record_task(instance)
            reason = message or f"Task '{workflow_id}.{task_id}' completed"
            if task_def.requires_approval:
                self._try_state_transition(
                    ProjectState.AWAITING_APPROVAL,
                    reason,
                    trigger=TransitionTrigger.TASK_OUTCOME,
                )
        else:
            instance.status = TaskStatus.FAILED
            instance.outcome_message = message
            instance.updated_at = now
            self._publish_event(
                EventType.TASK_FAILED,
                {
                    "workflow_id": workflow_id,
                    "task_id": task_id,
                    "message": message or "",
                },
            )
            reason = message or f"Task '{workflow_id}.{task_id}' failed"
            self._try_state_transition(
                ProjectState.FAILED,
                reason,
                trigger=TransitionTrigger.TASK_OUTCOME,
            )

        self._refresh_workflow(workflow_id)
        if success and derive_workflow_status(
            workflow,
            self._require_workflow_instance(workflow_id),
            self._tasks,
        ) == WorkflowStatus.COMPLETED:
            self._publish_event(
                EventType.WORKFLOW_COMPLETED,
                {"workflow_id": workflow_id},
            )
            self._try_state_transition(
                ProjectState.COMPLETED,
                f"Workflow '{workflow_id}' completed",
                trigger=TransitionTrigger.TASK_OUTCOME,
            )
        self._sync_project_state(reason)
        self._persist()
        return instance

    def _record_task(self, instance: TaskInstance) -> None:
        instance.status = TaskStatus.RECORDED
        instance.updated_at = _now_iso()

    def _refresh_all_workflows(self, *, persist: bool, sync_state: bool) -> None:
        for workflow_id in self._workflows:
            self._refresh_workflow(workflow_id, persist=False)
        if sync_state:
            self._sync_project_state("Workflow progress refreshed")
        if persist:
            self._persist()

    def _refresh_workflow(self, workflow_id: str, *, persist: bool = True) -> None:
        workflow = self._require_workflow(workflow_id)
        instance = self._require_workflow_instance(workflow_id)
        if instance.status in {WorkflowStatus.DEFINED, WorkflowStatus.CANCELLED}:
            return

        evaluate_task_readiness(workflow, self._tasks)
        new_status = derive_workflow_status(workflow, instance, self._tasks)
        if new_status != instance.status:
            instance.status = new_status
            instance.updated_at = _now_iso()
        if persist:
            self._persist()

    def _sync_project_state(self, reason: str) -> None:
        if self._state_engine is None:
            return

        target = self._derive_project_state()
        if target is None or target == self._state_engine.current:
            return
        apply_state_transition(
            self._state_engine,
            target,
            TransitionTrigger.WORKFLOW_RULE,
            reason,
        )

    def _derive_project_state(self) -> ProjectState | None:
        if not self._workflow_instances:
            return None

        progresses = [
            compute_progress(workflow, self._workflow_instances[workflow.id], self._tasks)
            for workflow in self._workflows.values()
            if workflow.id in self._workflow_instances
        ]
        if not progresses:
            return None

        if any(progress.failed > 0 for progress in progresses):
            return ProjectState.FAILED
        if any(progress.status == WorkflowStatus.BLOCKED for progress in progresses):
            return ProjectState.BLOCKED
        if all(progress.status == WorkflowStatus.COMPLETED for progress in progresses):
            return ProjectState.COMPLETED
        if any(progress.in_flight > 0 for progress in progresses):
            return ProjectState.EXECUTING
        if any(progress.ready > 0 for progress in progresses):
            return ProjectState.READY
        if any(
            progress.status in {WorkflowStatus.ACTIVATED, WorkflowStatus.IN_PROGRESS}
            for progress in progresses
        ):
            return ProjectState.PLANNING
        if any(progress.status == WorkflowStatus.DEFINED for progress in progresses):
            if self._state_engine and self._state_engine.current == ProjectState.INITIALIZED:
                return ProjectState.PLANNING
        return None

    def _try_state_transition(
        self,
        target: ProjectState,
        reason: str,
        *,
        trigger: TransitionTrigger = TransitionTrigger.WORKFLOW_RULE,
    ) -> None:
        if self._state_engine is None:
            return
        apply_state_transition(self._state_engine, target, trigger, reason)

    def _persist(self) -> None:
        save_progress(self._project_dir, self._workflow_instances, self._tasks.instances)

    def _require_workflow(self, workflow_id: str) -> WorkflowDefinition:
        workflow = self._workflows.get(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(f"Workflow '{workflow_id}' not found")
        return workflow

    def _require_workflow_instance(self, workflow_id: str) -> WorkflowInstance:
        if workflow_id not in self._workflow_instances:
            self._workflow_instances[workflow_id] = WorkflowInstance(workflow_id=workflow_id)
        return self._workflow_instances[workflow_id]

    def _publish_event(self, event_type: str, payload: dict) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            create_event(event_type, source="workflow-engine", payload=payload)
        )


def parse_task_ref(ref: str) -> tuple[str, str]:
    if "." not in ref:
        raise WorkflowError(f"Invalid task reference '{ref}' — expected workflow.task")
    workflow_id, task_id = ref.split(".", 1)
    if not workflow_id or not task_id:
        raise WorkflowError(f"Invalid task reference '{ref}' — expected workflow.task")
    return workflow_id, task_id


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
