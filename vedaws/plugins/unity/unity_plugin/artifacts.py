"""Unity artifact definitions and project layout checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

UNITY_WORKFLOW_ID = "unity"

UNITY_LAYOUT_DIRS: tuple[str, ...] = (
    "Assets",
    "Packages",
    "ProjectSettings",
    "Docs",
)

ARTIFACT_PATHS: tuple[tuple[str, str], ...] = (
    ("game-design", "Docs/game-design/GAME_DESIGN.md"),
    ("technical-design", "Docs/technical-design/TECHNICAL_DESIGN.md"),
    ("builds", "Docs/builds/README.md"),
    ("playtests", "Docs/playtests/PLAYTEST_LOG.md"),
)

TASK_ARTIFACT_MAP: dict[str, str] = {
    "concept": "game-design",
    "game-design": "game-design",
    "prototype": "technical-design",
    "gameplay": "technical-design",
    "ui": "technical-design",
    "testing": "playtests",
    "build": "builds",
    "release": "builds",
}


@dataclass(frozen=True)
class ArtifactStatus:
    artifact_id: str
    path: str
    exists: bool
    linked_task: str | None = None


@dataclass(frozen=True)
class LayoutStatus:
    path: str
    exists: bool


def list_layout_status(workspace: Path) -> list[LayoutStatus]:
    root = workspace.resolve()
    return [
        LayoutStatus(path=entry, exists=(root / entry).is_dir())
        for entry in UNITY_LAYOUT_DIRS
    ]


def list_artifact_status(workspace: Path) -> list[ArtifactStatus]:
    root = workspace.resolve()
    statuses: list[ArtifactStatus] = []
    for artifact_id, relative in ARTIFACT_PATHS:
        linked = _task_for_artifact(artifact_id)
        statuses.append(
            ArtifactStatus(
                artifact_id=artifact_id,
                path=relative.replace("\\", "/"),
                exists=(root / relative).is_file(),
                linked_task=linked,
            )
        )
    return statuses


def _task_for_artifact(artifact_id: str) -> str | None:
    for task_id, mapped in TASK_ARTIFACT_MAP.items():
        if mapped == artifact_id:
            return task_id
    return None


def format_layout_report(workspace: Path) -> str:
    lines = ["Unity project layout:", ""]
    for status in list_layout_status(workspace):
        mark = "ok" if status.exists else "missing"
        lines.append(f"  [{mark:<7}] {status.path}/")
    return "\n".join(lines)


def format_artifact_report(workspace: Path) -> str:
    lines = ["Unity documentation artifacts:", ""]
    for status in list_artifact_status(workspace):
        mark = "ok" if status.exists else "missing"
        task = f" (task: unity.{status.linked_task})" if status.linked_task else ""
        lines.append(f"  [{mark:<7}] {status.artifact_id:<18} {status.path}{task}")
    present = sum(1 for status in list_artifact_status(workspace) if status.exists)
    lines.extend(["", f"Present: {present} / {len(ARTIFACT_PATHS)}"])
    return "\n".join(lines)


def layout_is_valid(workspace: Path) -> bool:
    return all(status.exists for status in list_layout_status(workspace))
