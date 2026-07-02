"""Completion orchestration unit tests (§5.4 full sequence, §10.6)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import patch

from vespawd_executor.api.types import ExecutorContext
from vespawd_executor.orchestration.finalize import orchestrate_completion
from vespawd_executor.orchestration.types import CompleteOrchestrationResult
from vespawd_executor.paths.resolver import resolve_workspace_paths
from vespawd_executor.sync.handoff import HandoffFacts

TS = datetime(2026, 7, 2, 10, 0, 0, tzinfo=timezone.utc)


def _paths(fixture_workspace):
    return resolve_workspace_paths(fixture_workspace)


def _set_in_progress(paths) -> None:
    paths.current_task_path.write_text(
        "# Current Task\n\n**Status:** `in_progress`\n\n## Goal\n\nBuild service\n"
        "\n## Progress Log\n\n| Date | Update |\n|------|--------|\n",
        encoding="utf-8",
    )


def _ok_complete() -> CompleteOrchestrationResult:
    return CompleteOrchestrationResult(ok=True, project_state="documenting")


@patch("vespawd_executor.orchestration.finalize.orchestrate_phase_complete")
def test_completion_full_sequence(mock_pc, fixture_workspace) -> None:
    mock_pc.return_value = _ok_complete()
    paths = _paths(fixture_workspace)
    _set_in_progress(paths)
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))

    result = orchestrate_completion(
        paths,
        ctx,
        vedaws_task_id="software.implement",
        outcome="completed",
        goal="Build service",
        handoff_facts=HandoffFacts(features_done=["login"], database="MySQL"),
        acceptance=["login works"],
        changed_paths=["main/src/a.py"],
        closed_on=date(2026, 7, 2),
        synced_at=TS,
    )
    assert result.ok
    assert result.steps_completed == [
        "phase_complete",
        "handoff_refresh",
        "completed_log",
        "current_task_closeout",
    ]
    assert result.handoff_refreshed
    assert result.completed_log_created
    assert result.current_task_closed
    task_text = paths.current_task_path.read_text(encoding="utf-8")
    assert "**Status:** `idle`" in task_text
    assert "Phase complete (completed)" in task_text


@patch("vespawd_executor.orchestration.finalize.orchestrate_phase_complete")
def test_completion_stops_when_bridge_denies(mock_pc, fixture_workspace) -> None:
    mock_pc.return_value = CompleteOrchestrationResult(
        ok=False, blockers=["task_complete_denied"]
    )
    paths = _paths(fixture_workspace)
    _set_in_progress(paths)
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))

    result = orchestrate_completion(
        paths, ctx, vedaws_task_id="t", outcome="completed", goal="Build service",
        closed_on=date(2026, 7, 2), synced_at=TS,
    )
    assert not result.ok
    assert result.steps_completed == ["phase_complete"]
    assert not result.handoff_refreshed
    assert not result.completed_log_created


@patch("vespawd_executor.orchestration.finalize.orchestrate_phase_complete")
def test_completion_non_completed_outcome_skips_closeout(mock_pc, fixture_workspace) -> None:
    mock_pc.return_value = _ok_complete()
    paths = _paths(fixture_workspace)
    _set_in_progress(paths)
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))

    result = orchestrate_completion(
        paths, ctx, vedaws_task_id="t", outcome="blocked", goal="Build service",
        reason="dependency failure", closed_on=date(2026, 7, 2), synced_at=TS,
    )
    assert result.ok
    assert result.steps_completed == ["phase_complete"]
    assert not result.completed_log_created


@patch("vespawd_executor.orchestration.finalize.orchestrate_phase_complete")
def test_completion_idempotent(mock_pc, fixture_workspace) -> None:
    mock_pc.return_value = _ok_complete()
    paths = _paths(fixture_workspace)
    _set_in_progress(paths)
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    kwargs = dict(
        vedaws_task_id="software.implement",
        outcome="completed",
        goal="Build service",
        handoff_facts=HandoffFacts(features_done=["login"]),
        acceptance=["login works"],
        changed_paths=["main/src/a.py"],
        closed_on=date(2026, 7, 2),
        synced_at=TS,
    )
    first = orchestrate_completion(paths, ctx, **kwargs)
    handoff_after_first = (paths.pos_root / "docs" / "HANDOFF_FOR_DOCUMENTER.md").read_text(
        encoding="utf-8"
    )
    second = orchestrate_completion(paths, ctx, **kwargs)
    handoff_after_second = (paths.pos_root / "docs" / "HANDOFF_FOR_DOCUMENTER.md").read_text(
        encoding="utf-8"
    )
    assert first.completed_log_created is True
    assert second.completed_log_created is False
    assert handoff_after_first == handoff_after_second
