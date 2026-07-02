"""Resume mid-phase reader tests (§12.3)."""

from __future__ import annotations

from vespawd_executor.paths.resolver import resolve_workspace_paths
from vespawd_executor.recovery.resume import read_resume_state


def _paths(fixture_workspace):
    return resolve_workspace_paths(fixture_workspace)


def _write_task(paths, status: str, goal: str = "Build service") -> None:
    paths.current_task_path.write_text(
        f"# Current Task\n\n**Status:** `{status}`\n\n## Goal\n\n{goal}\n",
        encoding="utf-8",
    )


def test_resumable_in_progress(fixture_workspace) -> None:
    paths = _paths(fixture_workspace)
    _write_task(paths, "in_progress")
    state = read_resume_state(paths)
    assert state.resumable
    assert state.task_status == "in_progress"
    assert state.task_goal == "Build service"
    assert state.has_current_task
    assert state.has_status
    assert state.has_project_context
    assert state.product_name == "testapp"


def test_resumable_blocked(fixture_workspace) -> None:
    paths = _paths(fixture_workspace)
    _write_task(paths, "blocked")
    state = read_resume_state(paths)
    assert state.resumable


def test_not_resumable_idle(fixture_workspace) -> None:
    paths = _paths(fixture_workspace)
    _write_task(paths, "idle")
    state = read_resume_state(paths)
    assert not state.resumable
    assert state.task_status == "idle"


def test_missing_current_task_warns(fixture_workspace) -> None:
    paths = _paths(fixture_workspace)
    paths.current_task_path.unlink()
    state = read_resume_state(paths)
    assert not state.resumable
    assert not state.has_current_task
    assert any("current_task.md missing" in w for w in state.warnings)


def test_missing_status_and_context_warn(fixture_workspace) -> None:
    paths = _paths(fixture_workspace)
    _write_task(paths, "in_progress")
    paths.status_path.unlink()
    paths.project_context_path.unlink()
    state = read_resume_state(paths)
    assert not state.has_status
    assert not state.has_project_context
    assert any("status.md missing" in w for w in state.warnings)
    assert any("project_context.md missing" in w for w in state.warnings)


def test_deterministic(fixture_workspace) -> None:
    paths = _paths(fixture_workspace)
    _write_task(paths, "in_progress")
    assert read_resume_state(paths).to_dict() == read_resume_state(paths).to_dict()
