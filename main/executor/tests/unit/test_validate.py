"""Startup validation tests (§3.4)."""

from __future__ import annotations

from pathlib import Path

from vespawd_executor.api.types import SessionOptions
from vespawd_executor.paths.resolver import resolve_workspace_paths
from vespawd_executor.startup.validate import validate_concurrent_task, validate_startup


def test_layout_mismatch_warning(fixture_workspace: Path) -> None:
    ctx_path = fixture_workspace / "paws022" / ".ai" / "project_context.md"
    text = ctx_path.read_text(encoding="utf-8").replace("sidecar", "integrated")
    ctx_path.write_text(text, encoding="utf-8")

    paths = resolve_workspace_paths(fixture_workspace)
    result = validate_startup(paths, SessionOptions())
    assert result.passed
    assert any("Layout mismatch" in w for w in result.warnings)


def test_concurrent_task_blocks_without_supersede(fixture_workspace: Path) -> None:
    paths = resolve_workspace_paths(fixture_workspace)
    paths.current_task_path.parent.mkdir(parents=True, exist_ok=True)
    paths.current_task_path.write_text(
        "Status: in_progress\n\n### Goal\nBuild auth module\n",
        encoding="utf-8",
    )
    result = validate_concurrent_task(paths, SessionOptions(), "Implement payments API")
    assert not result.passed
    assert result.blockers


def test_concurrent_task_allows_supersede(fixture_workspace: Path) -> None:
    paths = resolve_workspace_paths(fixture_workspace)
    paths.current_task_path.write_text(
        "Status: in_progress\n\n### Goal\nBuild auth module\n",
        encoding="utf-8",
    )
    result = validate_concurrent_task(
        paths,
        SessionOptions(supersede_active_task=True),
        "Implement payments API",
    )
    assert result.passed
