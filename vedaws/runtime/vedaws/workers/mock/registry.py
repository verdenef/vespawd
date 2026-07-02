"""Register bundled mock workers."""

from __future__ import annotations

from vedaws.workers.interface import ExecutableWorker
from vedaws.workers.mock.echo import EchoWorker
from vedaws.workers.mock.failure import FailureWorker
from vedaws.workers.mock.sleep import SleepWorker
from vedaws.workers.mock.success import SuccessWorker
from vedaws.workers.registry import WorkerRegistry


def create_mock_workers() -> list[ExecutableWorker]:
    return [
        EchoWorker(),
        SleepWorker(),
        SuccessWorker(),
        FailureWorker(),
    ]


def register_mock_workers(registry: WorkerRegistry) -> int:
    """Register or replace mock workers in the registry. Returns count registered."""
    count = 0
    for worker in create_mock_workers():
        registry.register(worker)
        count += 1
    return count
