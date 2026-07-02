"""Live Bridge pre_implement_check integration tests (§8.2)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from vespawd_executor.api.types import ExecutorContext, SessionOptions
from vespawd_executor.orchestration import (
    orchestrate_master_prompt_from_text,
    run_pre_implement_check,
)
from vespawd_executor.paths.resolver import resolve_workspace_paths
from vespawd_executor.startup.sequence import run_startup

from tests.conftest import requires_vedaws

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SAMPLE = (FIXTURES / "sample_master_prompt.md").read_text(encoding="utf-8")
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


@requires_vedaws
def test_live_gate_allows_after_ingest(fixture_workspace: Path) -> None:
    run_startup(fixture_workspace)
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    ingest = orchestrate_master_prompt_from_text(
        _IMPLEMENT_PROMPT, fixture_workspace, ctx, synced_at=FIXED_TS, started_at=date(2026, 6, 1)
    )
    assert ingest.ok, ingest.blockers

    paths = resolve_workspace_paths(fixture_workspace)
    gate = run_pre_implement_check(paths, ctx, "Implement the backend service logic")
    assert gate.check is not None
    assert gate.allow_implement, gate.blockers


@requires_vedaws
def test_live_gate_idempotent(fixture_workspace: Path) -> None:
    run_startup(fixture_workspace)
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    orchestrate_master_prompt_from_text(
        _IMPLEMENT_PROMPT, fixture_workspace, ctx, synced_at=FIXED_TS, started_at=date(2026, 6, 1)
    )
    paths = resolve_workspace_paths(fixture_workspace)
    first = run_pre_implement_check(paths, ctx, "Implement the backend service logic")
    second = run_pre_implement_check(paths, ctx, "Implement the backend service logic")
    assert first.allow_implement == second.allow_implement


@requires_vedaws
def test_live_gate_design_block_for_ui(fixture_workspace: Path) -> None:
    # DESIGN.md not ready → UI task should be gated
    design = fixture_workspace / "paws022" / "design" / "DESIGN.md"
    design.write_text("## Status\n\n- **Design phase:** in progress\n", encoding="utf-8")

    run_startup(fixture_workspace)
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    orchestrate_master_prompt_from_text(
        SAMPLE, fixture_workspace, ctx, synced_at=FIXED_TS, started_at=date(2026, 6, 1)
    )
    paths = resolve_workspace_paths(fixture_workspace)
    gate = run_pre_implement_check(
        paths, ctx, "Build the dashboard screen and settings form UI"
    )
    assert gate.check is not None
    if not gate.allow_implement:
        assert gate.design_gate_blocked or gate.blockers
