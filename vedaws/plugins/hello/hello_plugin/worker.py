"""Hello worker — reference plugin worker contribution."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from vedaws.workers.execution import TaskDispatch, TaskOutcome
from vedaws.workers.interface import ExecutableWorker
from vedaws.workers.models import WorkerCapability, WorkerHealthReport, WorkerMetadata
from vedaws.workers.status import WorkerHealth, WorkerStatus
from vedaws.workers.types import WorkerType


class HelloWorker(ExecutableWorker):
    """Executable worker contributed by the Hello plugin."""

    def __init__(self) -> None:
        self._metadata = WorkerMetadata(
            id="hello.worker",
            name="Hello Worker",
            description="Greets and completes hello-capability tasks",
            version="0.1.0",
            worker_type=WorkerType.TOOL,
            capabilities=(WorkerCapability(work_type="hello", scope="greeting"),),
            status=WorkerStatus.AVAILABLE,
            provider="hello-plugin",
            source_path=Path("hello_plugin"),
        )

    @property
    def metadata(self) -> WorkerMetadata:
        return self._metadata

    def health_check(self) -> WorkerHealthReport:
        return WorkerHealthReport(
            worker_id=self.id,
            health=WorkerHealth.HEALTHY,
            message="Hello worker ready",
        )

    def _set_status(self, status: WorkerStatus) -> None:
        self._metadata = replace(self._metadata, status=status)

    def execute(self, dispatch: TaskDispatch) -> TaskOutcome:
        return TaskOutcome.success(
            message="Hello from the Hello plugin!",
            task_key=dispatch.key,
            capability=dispatch.task.capability,
        )
