"""Full PAWS sync engine tests (§5.3)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from vespawd_executor.parse import parse_master_prompt
from vespawd_executor.paths.resolver import resolve_workspace_paths
from vespawd_executor.sync import sync_paws_files

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SAMPLE = (FIXTURES / "sample_master_prompt.md").read_text(encoding="utf-8")


FIXED_TS = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_sync_paws_files_writes_all_artifacts(fixture_workspace: Path) -> None:
    parsed = parse_master_prompt(SAMPLE)
    assert parsed.ok and parsed.parsed
    paths = resolve_workspace_paths(fixture_workspace)
    result = sync_paws_files(
        parsed.parsed,
        paths,
        repo_path=str(fixture_workspace),
        started_at=date(2026, 6, 1),
        synced_at=FIXED_TS,
    )
    assert result.ok
    assert len(result.files_written) == 4
    assert result.backlog_appended == 2

    context = paths.project_context_path.read_text(encoding="utf-8")
    assert "CourseReg" in context
    assert "sidecar" in context

    task = paths.current_task_path.read_text(encoding="utf-8")
    assert "in_progress" in task
    assert "MVP scope" in task

    backlog = (paths.pos_root / "tasks" / "backlog.md").read_text(encoding="utf-8")
    assert "Architecture" in backlog

    handoff = (paths.pos_root / "docs" / "HANDOFF_FOR_DOCUMENTER.md").read_text(encoding="utf-8")
    assert "CourseReg" in handoff


def test_sync_idempotent(fixture_workspace: Path) -> None:
    parsed = parse_master_prompt(SAMPLE)
    assert parsed.parsed
    paths = resolve_workspace_paths(fixture_workspace)
    sync_paws_files(
        parsed.parsed,
        paths,
        started_at=date(2026, 6, 1),
        synced_at=FIXED_TS,
    )
    snapshots = {
        p: p.read_text(encoding="utf-8")
        for p in [
            paths.project_context_path,
            paths.current_task_path,
            paths.pos_root / "tasks" / "backlog.md",
            paths.pos_root / "docs" / "HANDOFF_FOR_DOCUMENTER.md",
        ]
    }
    second = sync_paws_files(
        parsed.parsed,
        paths,
        started_at=date(2026, 6, 1),
        synced_at=FIXED_TS,
    )
    assert second.backlog_appended == 0
    for path, content in snapshots.items():
        assert path.read_text(encoding="utf-8") == content
