"""Worker manifest parsing."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from vedaws.workers.models import WorkerCapability, WorkerMetadata
from vedaws.workers.status import WorkerStatus
from vedaws.workers.types import WorkerType

WORKER_MANIFEST_FILE = "vedaws.worker.toml"


def parse_worker_manifest(path: Path) -> tuple[WorkerMetadata | None, str | None]:
    """Parse a worker manifest. Returns (metadata, error_reason)."""
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except OSError as exc:
        return None, f"cannot read manifest: {exc}"
    except tomllib.TOMLDecodeError as exc:
        return None, f"invalid TOML: {exc}"

    worker = data.get("worker", data)
    worker_id = str(worker.get("id", "")).strip()
    if not worker_id:
        return None, "missing worker id"

    worker_type = WorkerType.parse(str(worker.get("type", "")))
    if worker_type is None:
        return None, f"invalid worker type: {worker.get('type')!r}"

    capabilities = _parse_capabilities(data.get("capabilities", []))
    if not capabilities:
        return None, "at least one capability is required"

    metadata = WorkerMetadata(
        id=worker_id,
        name=str(worker.get("name", worker_id)),
        description=str(worker.get("description", "")),
        version=str(worker.get("version", "0.0.0")),
        worker_type=worker_type,
        capabilities=tuple(capabilities),
        status=WorkerStatus.AVAILABLE,
        provider=_optional_str(worker.get("provider")),
        source_path=path.parent,
    )
    return metadata, None


def _parse_capabilities(raw: Any) -> list[WorkerCapability]:
    if not isinstance(raw, list):
        return []

    capabilities: list[WorkerCapability] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        work_type = str(entry.get("work_type", "")).strip()
        if not work_type:
            continue
        capabilities.append(
            WorkerCapability(
                work_type=work_type,
                scope=str(entry.get("scope", "general")),
                constraints=str(entry.get("constraints", "")),
                risk=str(entry.get("risk", "low")),
                available=bool(entry.get("available", True)),
            )
        )
    return capabilities


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
