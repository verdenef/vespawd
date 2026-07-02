"""Manifest-backed worker implementation for discovery and placeholders."""

from __future__ import annotations

from dataclasses import replace

from vedaws.workers.interface import Worker
from vedaws.workers.models import WorkerHealthReport, WorkerMetadata
from vedaws.workers.status import WorkerHealth, WorkerStatus


class ManifestWorker(Worker):
    """Worker defined by a manifest file without a runtime executor binding."""

    def __init__(self, metadata: WorkerMetadata) -> None:
        self._metadata = metadata

    @property
    def metadata(self) -> WorkerMetadata:
        return self._metadata

    def health_check(self) -> WorkerHealthReport:
        if self._metadata.status == WorkerStatus.INVALID:
            return WorkerHealthReport(
                worker_id=self._metadata.id,
                health=WorkerHealth.UNHEALTHY,
                message="Worker manifest is invalid",
            )
        if self._metadata.status == WorkerStatus.UNAVAILABLE:
            return WorkerHealthReport(
                worker_id=self._metadata.id,
                health=WorkerHealth.DEGRADED,
                message="Worker is unavailable",
            )
        if self._metadata.status == WorkerStatus.RETIRED:
            return WorkerHealthReport(
                worker_id=self._metadata.id,
                health=WorkerHealth.UNHEALTHY,
                message="Worker is retired",
            )
        if not self._metadata.capabilities:
            return WorkerHealthReport(
                worker_id=self._metadata.id,
                health=WorkerHealth.DEGRADED,
                message="Worker declares no capabilities",
            )
        return WorkerHealthReport(
            worker_id=self._metadata.id,
            health=WorkerHealth.HEALTHY,
            message="Manifest-only worker (no runtime executor)",
        )

    def _set_status(self, status: WorkerStatus) -> None:
        self._metadata = replace(self._metadata, status=status)
