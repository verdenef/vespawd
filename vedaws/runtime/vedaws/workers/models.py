"""Worker metadata and capability models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from vedaws.workers.status import WorkerHealth, WorkerStatus
from vedaws.workers.types import WorkerType


@dataclass(frozen=True)
class WorkerCapability:
    work_type: str
    scope: str = "general"
    constraints: str = ""
    risk: str = "low"
    available: bool = True

    @property
    def key(self) -> str:
        return f"{self.work_type}:{self.scope}"


@dataclass(frozen=True)
class WorkerMetadata:
    id: str
    name: str
    description: str
    version: str
    worker_type: WorkerType
    capabilities: tuple[WorkerCapability, ...]
    status: WorkerStatus = WorkerStatus.REGISTERED
    provider: str | None = None
    source_path: Path | None = None

    @property
    def display_name(self) -> str:
        return self.name or self.id

    @property
    def capability_labels(self) -> list[str]:
        return [capability.work_type for capability in self.capabilities]


@dataclass(frozen=True)
class WorkerHealthReport:
    worker_id: str
    health: WorkerHealth
    message: str = ""

    @property
    def healthy(self) -> bool:
        return self.health == WorkerHealth.HEALTHY


@dataclass
class InvalidWorkerRecord:
    path: Path
    reason: str


@dataclass
class DuplicateWorkerRecord:
    worker_id: str
    kept_path: Path
    skipped_path: Path
