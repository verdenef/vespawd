"""Worker dispatcher — assign READY tasks and track execution lifecycle."""

from __future__ import annotations

import logging
from pathlib import Path

from vedaws.ai.service import AIService
from vedaws.dispatch.matcher import select_worker
from vedaws.dispatch.models import DispatchResult, DispatchStatus
from vedaws.events.bus import EventBus
from vedaws.events.model import create_event
from vedaws.events.types import EventType
from vedaws.project.state.eligibility import allows_dispatch, dispatch_blocked_reason
from vedaws.project.state.states import ProjectState
from vedaws.workers.execution import TaskDispatch
from vedaws.workers.ai_worker import AIExecutableWorker
from vedaws.workers.interface import ExecutableWorker
from vedaws.workers.registry import WorkerRegistry
from vedaws.workers.status import WorkerStatus
from vedaws.workflow.engine import WorkflowEngine
from vedaws.workflow.models import TaskDefinition
from vedaws.workflow.states import TaskStatus

logger = logging.getLogger("vedaws.dispatch")


class WorkerDispatcher:
    """Selects compatible workers and executes READY tasks."""

    def __init__(
        self,
        workflow_engine: WorkflowEngine,
        worker_registry: WorkerRegistry,
        *,
        project_name: str = "",
        workspace: Path | None = None,
        ai_service: AIService | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._workflow = workflow_engine
        self._workers = worker_registry
        self._project_name = project_name
        self._workspace = workspace
        self._ai_service = ai_service
        self._event_bus = event_bus

    @property
    def workflow_engine(self) -> WorkflowEngine:
        return self._workflow

    @property
    def worker_registry(self) -> WorkerRegistry:
        return self._workers

    def set_ai_service(self, service: AIService | None) -> None:
        self._ai_service = service

    def list_ready_tasks(self) -> list:
        return self._workflow.task_registry.list_ready()

    def find_worker_for_task(
        self,
        task_def: TaskDefinition,
        *,
        preferred_worker_id: str | None = None,
    ) -> ExecutableWorker | None:
        return select_worker(
            self._workers,
            task_def,
            preferred_worker_id=preferred_worker_id,
        )

    def dispatch_and_execute(
        self,
        workflow_id: str,
        task_id: str,
        *,
        worker_id: str | None = None,
    ) -> DispatchResult:
        task_def = self._workflow.task_registry.get_definition(workflow_id, task_id)
        if task_def is None:
            return DispatchResult(
                status=DispatchStatus.NO_TASK,
                workflow_id=workflow_id,
                task_id=task_id,
                message=f"Task '{workflow_id}.{task_id}' not found",
            )

        instance = self._workflow.task_registry.get_instance(workflow_id, task_id)
        if instance is None or instance.status != TaskStatus.READY:
            status = instance.status.value if instance else "missing"
            return DispatchResult(
                status=DispatchStatus.SKIPPED,
                workflow_id=workflow_id,
                task_id=task_id,
                message=f"Task not ready (status={status})",
            )

        worker = self.find_worker_for_task(task_def, preferred_worker_id=worker_id)
        if worker is None:
            return DispatchResult(
                status=DispatchStatus.NO_WORKER,
                workflow_id=workflow_id,
                task_id=task_id,
                message=f"No compatible worker for capability '{task_def.capability}'",
            )

        if worker_id and worker.id != worker_id:
            return DispatchResult(
                status=DispatchStatus.INCOMPATIBLE,
                workflow_id=workflow_id,
                task_id=task_id,
                worker_id=worker_id,
                message=f"Worker '{worker_id}' cannot execute capability '{task_def.capability}'",
            )

        blocked = self._dispatch_blocked()
        if blocked is not None:
            return DispatchResult(
                status=DispatchStatus.SKIPPED,
                workflow_id=workflow_id,
                task_id=task_id,
                message=blocked,
            )

        return self._execute_with_worker(workflow_id, task_id, task_def, worker)

    def _dispatch_blocked(self) -> str | None:
        engine = self._workflow.state_engine
        if engine is None:
            return None
        current = engine.current
        if not allows_dispatch(current):
            return dispatch_blocked_reason(current)
        if current != ProjectState.EXECUTING:
            self._workflow.ensure_executing("Preparing for task dispatch")
            if not allows_dispatch(engine.current) and engine.current != ProjectState.EXECUTING:
                return dispatch_blocked_reason(engine.current)
        return None

    def _execute_with_worker(
        self,
        workflow_id: str,
        task_id: str,
        task_def: TaskDefinition,
        worker: ExecutableWorker,
    ) -> DispatchResult:
        task_key = f"{workflow_id}.{task_id}"
        logger.info("Dispatching %s to worker %s", task_key, worker.id)

        try:
            self._workflow.mark_dispatched(workflow_id, task_id, worker.id)
            worker.set_status(WorkerStatus.ASSIGNED)
            self._workflow.mark_running(workflow_id, task_id)
            worker.set_status(WorkerStatus.EXECUTING)
            self._workflow.ensure_executing(f"Task '{task_key}' running")
            self._publish_worker_event(
                EventType.WORKER_STARTED,
                worker.id,
                workflow_id,
                task_id,
            )

            dispatch = TaskDispatch(
                workflow_id=workflow_id,
                task_id=task_id,
                task=task_def,
                project_name=self._project_name,
                instructions=str(self._workspace) if self._workspace else "",
            )
            if isinstance(worker, AIExecutableWorker) and self._ai_service is not None:
                worker.bind_ai_service(self._ai_service)
            outcome = worker.execute(dispatch)
            success = outcome.status.is_success
            message = outcome.message or outcome.status.value

            self._workflow.record_worker_outcome(
                workflow_id,
                task_id,
                success=success,
                message=message,
            )
            self._workflow.sync_project_state(f"Task '{task_key}' outcome recorded")
            self._publish_worker_event(
                EventType.WORKER_COMPLETED,
                worker.id,
                workflow_id,
                task_id,
                success=success,
                message=message,
            )

            logger.info(
                "Task %s finished via %s — success=%s",
                task_key,
                worker.id,
                success,
            )
            return DispatchResult(
                status=DispatchStatus.DISPATCHED,
                workflow_id=workflow_id,
                task_id=task_id,
                worker_id=worker.id,
                message=message,
                success=success,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Dispatch failed for %s", task_key)
            self._best_effort_record_failure(workflow_id, task_id, str(exc))
            return DispatchResult(
                status=DispatchStatus.ERROR,
                workflow_id=workflow_id,
                task_id=task_id,
                worker_id=worker.id,
                message=str(exc),
                success=False,
            )
        finally:
            worker.set_status(WorkerStatus.AVAILABLE)

    def _publish_worker_event(
        self,
        event_type: str,
        worker_id: str,
        workflow_id: str,
        task_id: str,
        *,
        success: bool | None = None,
        message: str = "",
    ) -> None:
        if self._event_bus is None:
            return
        payload: dict = {
            "worker_id": worker_id,
            "workflow_id": workflow_id,
            "task_id": task_id,
            "task_key": f"{workflow_id}.{task_id}",
        }
        if success is not None:
            payload["success"] = success
            payload["message"] = message
        self._event_bus.publish(
            create_event(event_type, source="worker-dispatcher", payload=payload)
        )

    def _best_effort_record_failure(
        self, workflow_id: str, task_id: str, message: str
    ) -> None:
        """Record failure outcome only when task was already running.

        This keeps failure handling consistent after execution-time exceptions while
        avoiding secondary exceptions from masking the original dispatch error.
        """
        try:
            instance = self._workflow.task_registry.get_instance(workflow_id, task_id)
            if instance and instance.status == TaskStatus.RUNNING:
                self._workflow.record_worker_outcome(
                    workflow_id,
                    task_id,
                    success=False,
                    message=message,
                )
        except Exception as record_exc:  # noqa: BLE001
            logger.debug(
                "Unable to record failure outcome for %s.%s: %s",
                workflow_id,
                task_id,
                record_exc,
            )
