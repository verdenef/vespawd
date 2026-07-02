"""Worker registry — registration, lookup, and lifecycle management."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vedaws.events.bus import EventBus
from vedaws.events.model import create_event
from vedaws.events.types import EventType
from vedaws.ai.service import AIService
from vedaws.workers.discovery import WorkerDiscoveryResult, discover_workers
from vedaws.workers.interface import ExecutableWorker, Worker
from vedaws.workers.models import WorkerHealthReport
from vedaws.workers.status import WorkerStatus
from vedaws.workers.types import WorkerType


@dataclass
class WorkerRegistry:
    _workers: dict[str, Worker] = field(default_factory=dict)
    discovery: WorkerDiscoveryResult | None = None
    _event_bus: EventBus | None = None

    def attach_event_bus(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus

    @classmethod
    def from_discovery(cls, result: WorkerDiscoveryResult) -> WorkerRegistry:
        registry = cls(discovery=result)
        for worker in result.workers:
            registry.register(worker)
        return registry

    def register(self, worker: Worker) -> None:
        self._workers[worker.id] = worker
        if self._event_bus is not None:
            self._event_bus.publish(
                create_event(
                    EventType.WORKER_REGISTERED,
                    source="worker-registry",
                    payload={
                        "worker_id": worker.id,
                        "worker_type": worker.metadata.worker_type.value,
                        "provider": worker.metadata.provider,
                    },
                )
            )

    def unregister(self, worker_id: str) -> Worker | None:
        worker = self._workers.pop(worker_id, None)
        if worker is not None:
            worker.set_status(WorkerStatus.RETIRED)
        return worker

    def get(self, worker_id: str) -> Worker | None:
        return self._workers.get(worker_id)

    def list_workers(self) -> list[Worker]:
        return sorted(self._workers.values(), key=lambda worker: worker.id)

    def list_by_type(self, worker_type: WorkerType) -> list[Worker]:
        return [
            worker
            for worker in self.list_workers()
            if worker.metadata.worker_type == worker_type
        ]

    def find_by_capability(self, work_type: str, scope: str | None = None) -> list[Worker]:
        matches: list[Worker] = []
        for worker in self.list_workers():
            if worker.status not in {
                WorkerStatus.REGISTERED,
                WorkerStatus.AVAILABLE,
            }:
                continue
            for capability in worker.metadata.capabilities:
                if capability.work_type != work_type:
                    continue
                if scope is not None and capability.scope != scope:
                    continue
                if not capability.available:
                    continue
                matches.append(worker)
                break
        return matches

    def find_executable_by_capability(
        self, work_type: str, scope: str | None = None
    ) -> list[ExecutableWorker]:
        return [
            worker
            for worker in self.find_by_capability(work_type, scope)
            if isinstance(worker, ExecutableWorker)
        ]

    def list_executable(self) -> list[ExecutableWorker]:
        return [
            worker
            for worker in self.list_workers()
            if isinstance(worker, ExecutableWorker)
        ]

    def wire_ai_service(self, ai_service: AIService) -> int:
        """Bind AIService into all registered AI executable workers."""
        from vedaws.workers.ai_worker import AIExecutableWorker

        wired = 0
        for worker in self.list_executable():
            if isinstance(worker, AIExecutableWorker):
                worker.bind_ai_service(ai_service)
                wired += 1
        return wired

    def wire_skills(self, skills: list[Any]) -> int:
        """Bind registered plugin skill metadata into AI executable workers."""
        from vedaws.workers.ai_worker import AIExecutableWorker

        skill_map: dict[str, tuple[str, str]] = {}
        for skill in skills:
            skill_id = str(getattr(skill, "id", "")).strip()
            if not skill_id:
                continue
            skill_map[skill_id] = (
                str(getattr(skill, "name", skill_id)),
                str(getattr(skill, "description", "")),
            )

        wired = 0
        for worker in self.list_executable():
            if isinstance(worker, AIExecutableWorker):
                worker.bind_skills(skill_map)
                wired += 1
        return wired

    def health_reports(self) -> list[WorkerHealthReport]:
        return [worker.health_check() for worker in self.list_workers()]

    def mark_unavailable(self, worker_id: str) -> bool:
        worker = self.get(worker_id)
        if worker is None:
            return False
        worker.set_status(WorkerStatus.UNAVAILABLE)
        return True

    def mark_available(self, worker_id: str) -> bool:
        worker = self.get(worker_id)
        if worker is None:
            return False
        worker.set_status(WorkerStatus.AVAILABLE)
        return True

    @property
    def count(self) -> int:
        return len(self._workers)

    @property
    def invalid_count(self) -> int:
        if self.discovery is None:
            return 0
        return len(self.discovery.invalid)

    @property
    def duplicate_count(self) -> int:
        if self.discovery is None:
            return 0
        return len(self.discovery.duplicates)
