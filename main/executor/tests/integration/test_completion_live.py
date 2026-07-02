"""Live Bridge completion + pre_documenter integration tests (§5.4, §8.5, §13)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from vespawd_executor.api.types import ExecutorContext
from vespawd_executor.orchestration import (
    orchestrate_completion,
    orchestrate_master_prompt_from_text,
    orchestrate_pre_documenter,
)
from vespawd_executor.paths.resolver import resolve_workspace_paths
from vespawd_executor.startup.sequence import run_startup
from vespawd_executor.sync.handoff import HandoffFacts

from tests.conftest import requires_vedaws

FIXED_TS = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

_IMPLEMENT_PROMPT = """# POS MASTER PROMPT

## PROJECT BRIEF

Implement phase.

## PROJECT CONTEXT UPDATES

- **Product name:** CourseReg

## CURRENT TASK

Status: in_progress

### Goal

Implement the backend service logic in main/src/.

### Constraints

- Userspace: main/src/

### Acceptance criteria

- [x] service module created

### Notes

- Vedaws phase: software.implement

## BACKLOG ITEMS

- [ ] **Tests** — add tests

## EXECUTOR INSTRUCTIONS

1. Implement in main/src/
"""


def _prepare(fixture_workspace: Path) -> ExecutorContext:
    run_startup(fixture_workspace)
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    orchestrate_master_prompt_from_text(
        _IMPLEMENT_PROMPT, fixture_workspace, ctx, synced_at=FIXED_TS, started_at=date(2026, 6, 1)
    )
    return ctx


@requires_vedaws
def test_live_pre_documenter_runs(fixture_workspace: Path) -> None:
    ctx = _prepare(fixture_workspace)
    paths = resolve_workspace_paths(fixture_workspace)
    result = orchestrate_pre_documenter(paths, ctx)
    assert result.check is not None
    assert result.check.operation == "pre_documenter"


@requires_vedaws
def test_live_completion_sequence(fixture_workspace: Path) -> None:
    ctx = _prepare(fixture_workspace)
    paths = resolve_workspace_paths(fixture_workspace)
    result = orchestrate_completion(
        paths,
        ctx,
        vedaws_task_id="software.implement",
        outcome="completed",
        goal="Implement the backend service logic",
        handoff_facts=HandoffFacts(features_done=["service module created"], database="MySQL"),
        acceptance=["service module created"],
        changed_paths=["main/src/service.py"],
        closed_on=date(2026, 6, 1),
        synced_at=FIXED_TS,
    )
    assert result.phase_complete is not None
    assert "phase_complete" in result.steps_completed
    # Close-out writes only run if Bridge completion succeeds.
    if result.phase_complete.ok:
        assert result.handoff_refreshed
        assert (paths.pos_root / "tasks" / "completed").is_dir()
        assert "**Status:** `idle`" in paths.current_task_path.read_text(encoding="utf-8")


@requires_vedaws
def test_live_completion_idempotent_closeout(fixture_workspace: Path) -> None:
    ctx = _prepare(fixture_workspace)
    paths = resolve_workspace_paths(fixture_workspace)
    kwargs = dict(
        vedaws_task_id="software.implement",
        outcome="completed",
        goal="Implement the backend service logic",
        handoff_facts=HandoffFacts(features_done=["service module created"]),
        acceptance=["service module created"],
        changed_paths=["main/src/service.py"],
        closed_on=date(2026, 6, 1),
        synced_at=FIXED_TS,
    )
    first = orchestrate_completion(paths, ctx, **kwargs)
    if not (first.phase_complete and first.phase_complete.ok):
        return
    completed_dir = paths.pos_root / "tasks" / "completed"
    count_first = len(list(completed_dir.glob("*.md")))
    orchestrate_completion(paths, ctx, **kwargs)
    count_second = len(list(completed_dir.glob("*.md")))
    assert count_first == count_second
