"""Unit tests — projection engine (§11.1)."""

from __future__ import annotations

from pathlib import Path

from vespawd_bridge.cli.parse import VedawsSnapshot
from vespawd_bridge.manifest.loader import load_manifest
from vespawd_bridge.manifest.paths import resolve_paths
from vespawd_bridge.projection.engine import enrich_notes, write_status


def test_write_status_atomic(workspace_root: Path, tmp_path: Path) -> None:
    manifest, _ = load_manifest(workspace_root)
    assert manifest is not None
    paths = resolve_paths(workspace_root, manifest)
    status_copy = tmp_path / "status.md"
    paths = paths.__class__(
        **{**paths.__dict__, "status_path": status_copy}
    )
    rel, _ = write_status(
        paths,
        VedawsSnapshot(project_state="planning", active_task_id="software.implement"),
    )
    assert status_copy.is_file()
    text = status_copy.read_text(encoding="utf-8")
    assert "software.implement" in text
    assert "Do not edit manually" in text


def test_notes_idempotent(workspace_root: Path, tmp_path: Path) -> None:
    manifest, _ = load_manifest(workspace_root)
    paths = resolve_paths(workspace_root, manifest)
    task_copy = tmp_path / "current_task.md"
    task_copy.write_text("## Notes\n\n## Progress Log\n", encoding="utf-8")
    paths = paths.__class__(**{**paths.__dict__, "current_task_path": task_copy})
    enrich_notes(paths, vedaws_task_id="software.implement", project_state="executing")
    first = task_copy.read_text(encoding="utf-8")
    enrich_notes(paths, vedaws_task_id="software.implement", project_state="executing")
    second = task_copy.read_text(encoding="utf-8")
    assert first.count("**Vedaws phase:**") == 1
    assert second.count("**Vedaws phase:**") == 1
