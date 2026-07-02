"""Software artifact definitions and status."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SOFTWARE_WORKFLOW_ID = "software"

ARTIFACT_PATHS: tuple[tuple[str, str], ...] = (
    ("architecture", "docs/architecture/ARCHITECTURE.md"),
    ("api", "docs/api/API.md"),
    ("decisions", "docs/decisions/DECISIONS.md"),
    ("handoff", "docs/handoff/HANDOFF.md"),
)

TASK_ARTIFACT_MAP: dict[str, str] = {
    "scope": "architecture",
    "architecture": "architecture",
    "api-design": "api",
    "implement": "api",
    "test": "decisions",
    "review": "decisions",
    "handoff": "handoff",
}


@dataclass(frozen=True)
class ArtifactStatus:
    artifact_id: str
    path: str
    exists: bool
    linked_task: str | None = None


def list_artifact_status(workspace: Path) -> list[ArtifactStatus]:
    root = workspace.resolve()
    statuses: list[ArtifactStatus] = []
    for artifact_id, relative in ARTIFACT_PATHS:
        path = root / relative
        linked = _task_for_artifact(artifact_id)
        statuses.append(
            ArtifactStatus(
                artifact_id=artifact_id,
                path=relative.replace("\\", "/"),
                exists=path.is_file(),
                linked_task=linked,
            )
        )
    return statuses


def _task_for_artifact(artifact_id: str) -> str | None:
    for task_id, mapped in TASK_ARTIFACT_MAP.items():
        if mapped == artifact_id:
            return task_id
    return None


def format_artifact_report(workspace: Path) -> str:
    statuses = list_artifact_status(workspace)
    lines = ["Software artifacts:", ""]
    for status in statuses:
        mark = "ok" if status.exists else "missing"
        task = f" (task: software.{status.linked_task})" if status.linked_task else ""
        lines.append(f"  [{mark:<7}] {status.artifact_id:<14} {status.path}{task}")
    present = sum(1 for status in statuses if status.exists)
    lines.extend(["", f"Present: {present} / {len(statuses)}"])
    return "\n".join(lines)
