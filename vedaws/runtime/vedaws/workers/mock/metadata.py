"""Shared metadata helpers for mock workers."""

from __future__ import annotations

from pathlib import Path

from vedaws.workers.models import WorkerCapability, WorkerMetadata
from vedaws.workers.status import WorkerStatus
from vedaws.workers.types import WorkerType


def mock_metadata(
    *,
    id: str,
    name: str,
    description: str,
    capabilities: list[tuple[str, str]],
) -> WorkerMetadata:
    return WorkerMetadata(
        id=id,
        name=name,
        description=description,
        version="0.1.0",
        worker_type=WorkerType.TOOL,
        capabilities=tuple(
            WorkerCapability(work_type=work_type, scope=scope)
            for work_type, scope in capabilities
        ),
        status=WorkerStatus.AVAILABLE,
        provider="vedaws-mock",
        source_path=Path("mock"),
    )
