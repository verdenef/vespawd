"""Worker discovery, registry, and interface."""

from vedaws.workers.discovery import WorkerDiscoveryResult, discover_workers
from vedaws.workers.ai_worker import AIExecutableWorker
from vedaws.workers.execution import TaskDispatch, TaskOutcome, TaskOutcomeStatus
from vedaws.workers.interface import ExecutableWorker, Worker
from vedaws.workers.manifest import WORKER_MANIFEST_FILE, parse_worker_manifest
from vedaws.workers.models import (
    DuplicateWorkerRecord,
    InvalidWorkerRecord,
    WorkerCapability,
    WorkerHealthReport,
    WorkerMetadata,
)
from vedaws.workers.registry import WorkerRegistry
from vedaws.workers.status import WorkerHealth, WorkerStatus
from vedaws.workers.types import WorkerType

__all__ = [
    "WORKER_MANIFEST_FILE",
    "DuplicateWorkerRecord",
    "AIExecutableWorker",
    "ExecutableWorker",
    "InvalidWorkerRecord",
    "TaskDispatch",
    "TaskOutcome",
    "TaskOutcomeStatus",
    "Worker",
    "WorkerCapability",
    "WorkerDiscoveryResult",
    "WorkerHealth",
    "WorkerHealthReport",
    "WorkerMetadata",
    "WorkerRegistry",
    "WorkerStatus",
    "WorkerType",
    "discover_workers",
    "parse_worker_manifest",
]
