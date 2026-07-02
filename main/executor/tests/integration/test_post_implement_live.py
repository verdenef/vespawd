"""Live Bridge post_implement integration tests (§7 guard + §8.3)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from vespawd_executor.api.types import ExecutorContext
from vespawd_executor.orchestration import (
    orchestrate_master_prompt_from_text,
    orchestrate_post_implement,
)
from vespawd_executor.paths.resolver import resolve_workspace_paths
from vespawd_executor.startup.sequence import run_startup

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

- [ ] service module created

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
def test_live_post_implement_success(fixture_workspace: Path) -> None:
    ctx = _prepare(fixture_workspace)
    (fixture_workspace / "main" / "src" / "service.py").write_text("x = 1\n", encoding="utf-8")

    paths = resolve_workspace_paths(fixture_workspace)
    result = orchestrate_post_implement(
        paths, ctx, ["main/src/service.py"], logged_at=date(2026, 6, 1)
    )
    assert result.post_implement is not None
    assert "progress_log" in result.steps_completed
    assert "bridge.post_implement" in result.steps_completed
    task_text = paths.current_task_path.read_text(encoding="utf-8")
    assert "service.py" in task_text


@requires_vedaws
def test_live_post_implement_forbidden_blocks(fixture_workspace: Path) -> None:
    ctx = _prepare(fixture_workspace)
    paths = resolve_workspace_paths(fixture_workspace)
    result = orchestrate_post_implement(
        paths, ctx, ["paws022/.ai/executor_rules.md"], logged_at=date(2026, 6, 1)
    )
    assert not result.ok
    assert result.blockers
    assert not result.steps_completed


@requires_vedaws
def test_live_post_implement_idempotent(fixture_workspace: Path) -> None:
    # Executor idempotency scope = its own Progress Log row. The Bridge projection
    # engine additionally writes a live `Last_sync` timestamp snapshot into
    # current_task.md, so whole-file equality is not an Executor guarantee.
    ctx = _prepare(fixture_workspace)
    (fixture_workspace / "main" / "src" / "service.py").write_text("x = 1\n", encoding="utf-8")
    paths = resolve_workspace_paths(fixture_workspace)
    first = orchestrate_post_implement(
        paths, ctx, ["main/src/service.py"], logged_at=date(2026, 6, 1)
    )
    second = orchestrate_post_implement(
        paths, ctx, ["main/src/service.py"], logged_at=date(2026, 6, 1)
    )
    assert first.progress_logged is True
    assert second.progress_logged is False
    text = paths.current_task_path.read_text(encoding="utf-8")
    assert text.count("Implemented 1 file: main/src/service.py") == 1
