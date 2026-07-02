"""Capability matching between tasks and workers."""

from __future__ import annotations

from vedaws.workers.interface import ExecutableWorker
from vedaws.workers.registry import WorkerRegistry
from vedaws.workflow.models import TaskDefinition


def match_workers(
    registry: WorkerRegistry,
    task: TaskDefinition,
    *,
    preferred_worker_id: str | None = None,
) -> list[ExecutableWorker]:
    capability = task.capability.strip()
    if not capability:
        return []

    if preferred_worker_id:
        worker = registry.get(preferred_worker_id)
        if worker is None or not isinstance(worker, ExecutableWorker):
            return []
        if _worker_supports(worker, capability):
            return [worker]
        return []

    return registry.find_executable_by_capability(capability)


def _worker_supports(worker: ExecutableWorker, capability: str) -> bool:
    for cap in worker.metadata.capabilities:
        if cap.work_type == capability and cap.available:
            return True
    return False


def select_worker(
    registry: WorkerRegistry,
    task: TaskDefinition,
    *,
    preferred_worker_id: str | None = None,
) -> ExecutableWorker | None:
    """Select a compatible worker using deterministic ordering (worker id)."""
    matches = match_workers(registry, task, preferred_worker_id=preferred_worker_id)
    if not matches:
        return None
    return sorted(matches, key=lambda worker: worker.id)[0]
