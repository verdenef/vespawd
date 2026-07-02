"""PAWS scheduler writes (Executor Spec §5.3 step 1) and HANDOFF seed (step 4)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from vespawd_executor.parse.types import ParsedMasterPrompt
from vespawd_executor.paths.resolver import WorkspacePaths
from vespawd_executor.sync.backlog import append_backlog_items
from vespawd_executor.sync.current_task import write_current_task
from vespawd_executor.sync.handoff import seed_handoff
from vespawd_executor.sync.project_context import merge_project_context
from vespawd_executor.sync.types import PawsSyncResult


def _relative_path(path: Path, paths: WorkspacePaths) -> str:
    for base in (paths.pos_root, paths.workspace_root):
        try:
            return str(path.relative_to(base)).replace("\\", "/")
        except ValueError:
            continue
    return str(path)


def sync_paws_scheduler(
    parsed: ParsedMasterPrompt,
    paths: WorkspacePaths,
    *,
    started_at: date | None = None,
) -> PawsSyncResult:
    """Write project_context, current_task, backlog (§5.3 step 1). No Bridge, no HANDOFF."""
    result = PawsSyncResult(ok=True)

    context_path = paths.project_context_path
    _, ctx_warnings = merge_project_context(context_path, parsed.project_context)
    result.warnings.extend(ctx_warnings)
    result.files_written.append(_relative_path(context_path, paths))

    task_path = paths.current_task_path
    write_current_task(
        task_path,
        parsed.current_task,
        instruction_conflicts=parsed.instruction_conflicts,
        phase_hint=parsed.phase_hint,
        started_at=started_at,
    )
    result.files_written.append(_relative_path(task_path, paths))

    backlog_path = paths.pos_root / "tasks" / "backlog.md"
    appended, _ = append_backlog_items(backlog_path, parsed.backlog_items)
    result.backlog_appended = appended
    result.files_written.append(_relative_path(backlog_path, paths))

    result.files_written = list(dict.fromkeys(result.files_written))
    return result


def seed_handoff_from_parse(
    parsed: ParsedMasterPrompt,
    paths: WorkspacePaths,
    *,
    repo_path: str | None = None,
    synced_at: datetime | None = None,
) -> tuple[str, list[str]]:
    """Seed HANDOFF (§5.3 step 4)."""
    handoff_path = paths.pos_root / "docs" / "HANDOFF_FOR_DOCUMENTER.md"
    repo = repo_path or str(paths.workspace_root)
    return seed_handoff(
        handoff_path,
        parsed,
        repo_path=repo,
        timestamp=synced_at or datetime.now(timezone.utc),
    )


def sync_paws_files(
    parsed: ParsedMasterPrompt,
    paths: WorkspacePaths,
    *,
    repo_path: str | None = None,
    started_at: date | None = None,
    synced_at: datetime | None = None,
) -> PawsSyncResult:
    """
    Phase 3 compatibility: scheduler + HANDOFF in one call.

    Phase 4 orchestration uses sync_paws_scheduler + Bridge + seed_handoff_from_parse.
    """
    result = sync_paws_scheduler(parsed, paths, started_at=started_at)
    _, handoff_warnings = seed_handoff_from_parse(
        parsed, paths, repo_path=repo_path, synced_at=synced_at
    )
    result.warnings.extend(handoff_warnings)
    handoff_path = paths.pos_root / "docs" / "HANDOFF_FOR_DOCUMENTER.md"
    rel = _relative_path(handoff_path, paths)
    if rel not in result.files_written:
        result.files_written.append(rel)
    return result
