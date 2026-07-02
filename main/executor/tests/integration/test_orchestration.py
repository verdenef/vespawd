"""Live Bridge orchestration integration tests."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from vespawd_executor.api.types import ExecutorContext
from vespawd_executor.orchestration import orchestrate_master_prompt_from_text, orchestrate_phase_complete
from vespawd_executor.paths.resolver import resolve_workspace_paths
from vespawd_executor.startup.sequence import run_startup

from tests.conftest import requires_vedaws

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SAMPLE = (FIXTURES / "sample_master_prompt.md").read_text(encoding="utf-8")
FIXED_TS = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


@requires_vedaws
def test_live_ingest_orchestration(fixture_workspace: Path) -> None:
    run_startup(fixture_workspace)
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = orchestrate_master_prompt_from_text(
        SAMPLE,
        fixture_workspace,
        ctx,
        started_at=date(2026, 6, 1),
        synced_at=FIXED_TS,
    )
    assert result.ok, result.blockers
    assert result.ingest is not None
    assert result.sync_status is not None
    assert "software.scope" in (result.vedaws_task_id or "")
    status_path = fixture_workspace / "paws022" / "tasks" / "status.md"
    assert status_path.is_file()


@requires_vedaws
def test_live_ingest_idempotent(fixture_workspace: Path) -> None:
    run_startup(fixture_workspace)
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    first = orchestrate_master_prompt_from_text(
        SAMPLE, fixture_workspace, ctx, synced_at=FIXED_TS, started_at=date(2026, 6, 1)
    )
    second = orchestrate_master_prompt_from_text(
        SAMPLE, fixture_workspace, ctx, synced_at=FIXED_TS, started_at=date(2026, 6, 1)
    )
    assert first.ok and second.ok
    assert second.paws_sync and second.paws_sync.backlog_appended == 0


@requires_vedaws
def test_live_phase_complete_orchestration(fixture_workspace: Path) -> None:
    run_startup(fixture_workspace)
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    ingest = orchestrate_master_prompt_from_text(
        SAMPLE, fixture_workspace, ctx, synced_at=FIXED_TS, started_at=date(2026, 6, 1)
    )
    assert ingest.ok, ingest.blockers

    paths = resolve_workspace_paths(fixture_workspace)
    complete = orchestrate_phase_complete(
        paths,
        ctx,
        {
            "vedaws_task_id": ingest.vedaws_task_id or "software.scope",
            "outcome": "completed",
            "human_gate": True,
        },
    )
    assert complete.ok, complete.blockers
    assert complete.post_phase_complete is not None
    assert complete.sync_status is not None
