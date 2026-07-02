"""Worker discovery from configured search paths."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from vedaws.config.schema import VedawsConfig
from vedaws.workers.interface import Worker
from vedaws.workers.manifest import WORKER_MANIFEST_FILE, parse_worker_manifest
from vedaws.workers.manifest_worker import ManifestWorker
from vedaws.workers.models import DuplicateWorkerRecord, InvalidWorkerRecord

logger = logging.getLogger("vedaws.workers")


@dataclass
class WorkerDiscoveryResult:
    workers: list[Worker] = field(default_factory=list)
    invalid: list[InvalidWorkerRecord] = field(default_factory=list)
    duplicates: list[DuplicateWorkerRecord] = field(default_factory=list)

    @property
    def worker_count(self) -> int:
        return len(self.workers)


def discover_workers(config: VedawsConfig) -> WorkerDiscoveryResult:
    if not config.workers.enabled:
        logger.info("Worker discovery disabled by configuration")
        return WorkerDiscoveryResult()

    result = WorkerDiscoveryResult()
    seen_ids: dict[str, Path] = {}

    for search_path in config.workers.search_paths:
        root = Path(search_path).expanduser()
        if not root.exists():
            logger.debug("Worker search path does not exist: %s", root)
            continue
        for manifest_path in _find_manifests(root):
            _register_manifest(manifest_path, seen_ids, result)

    result.workers.sort(key=lambda worker: worker.id)
    logger.info(
        "Discovered %d worker(s), %d invalid, %d duplicate(s)",
        result.worker_count,
        len(result.invalid),
        len(result.duplicates),
    )
    return result


def _find_manifests(root: Path) -> list[Path]:
    manifests: list[Path] = []

    direct = root / WORKER_MANIFEST_FILE
    if direct.is_file():
        manifests.append(direct)

    if not root.is_dir():
        return manifests

    for path in sorted(root.rglob(WORKER_MANIFEST_FILE)):
        if path not in manifests:
            manifests.append(path)

    return manifests


def _register_manifest(
    manifest_path: Path,
    seen_ids: dict[str, Path],
    result: WorkerDiscoveryResult,
) -> None:
    metadata, error = parse_worker_manifest(manifest_path)
    if error or metadata is None:
        result.invalid.append(InvalidWorkerRecord(path=manifest_path, reason=error or "unknown error"))
        logger.warning("Invalid worker manifest %s: %s", manifest_path, error)
        return

    if metadata.id in seen_ids:
        result.duplicates.append(
            DuplicateWorkerRecord(
                worker_id=metadata.id,
                kept_path=seen_ids[metadata.id],
                skipped_path=manifest_path,
            )
        )
        logger.warning(
            "Duplicate worker id '%s' at %s — skipping",
            metadata.id,
            manifest_path,
        )
        return

    seen_ids[metadata.id] = manifest_path
    result.workers.append(ManifestWorker(metadata))
