"""Base class for mock workers."""

from __future__ import annotations

from dataclasses import replace

from vedaws.workers.execution import TaskDispatch, TaskOutcome
from vedaws.workers.interface import ExecutableWorker
from vedaws.workers.models import WorkerHealthReport, WorkerMetadata
from vedaws.workers.status import WorkerHealth, WorkerStatus


class MockWorker(ExecutableWorker):
    """In-process mock worker for orchestration validation."""

    def __init__(self, metadata: WorkerMetadata) -> None:
        self._metadata = metadata

    @property
    def metadata(self) -> WorkerMetadata:
        return self._metadata

    def health_check(self) -> WorkerHealthReport:
        if self._metadata.status in {WorkerStatus.ASSIGNED, WorkerStatus.EXECUTING}:
            return WorkerHealthReport(
                worker_id=self._metadata.id,
                health=WorkerHealth.DEGRADED,
                message=f"Worker busy ({self._metadata.status.value})",
            )
        return WorkerHealthReport(
            worker_id=self._metadata.id,
            health=WorkerHealth.HEALTHY,
            message="Mock worker ready",
        )

    def _set_status(self, status: WorkerStatus) -> None:
        self._metadata = replace(self._metadata, status=status)
