"""Completion orchestration (Executor Spec §5.4 full sequence + §10.6 close-out)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from vespawd_executor.api.types import ExecutorContext
from vespawd_executor.orchestration.complete import orchestrate_phase_complete
from vespawd_executor.orchestration.types import CompletionResult
from vespawd_executor.paths.resolver import WorkspacePaths
from vespawd_executor.sync.completed import write_completed_log
from vespawd_executor.sync.current_task import set_task_status
from vespawd_executor.sync.handoff import HandoffFacts, refresh_handoff
from vespawd_executor.sync.progress_log import append_progress_entry


def orchestrate_completion(
    paths: WorkspacePaths,
    ctx: ExecutorContext,
    *,
    vedaws_task_id: str,
    outcome: str,
    goal: str,
    handoff_facts: HandoffFacts | None = None,
    acceptance: list[str] | None = None,
    changed_paths: list[str] | None = None,
    reason: str | None = None,
    human_gate: bool = True,
    repo_path: str | None = None,
    closed_on: date | None = None,
    synced_at: datetime | None = None,
) -> CompletionResult:
    """
    Full completion sequence (§5.4):
      2. bridge.post_phase_complete   (via orchestrate_phase_complete)
      3. bridge.sync_status           (via orchestrate_phase_complete)
      4. Executor refreshes HANDOFF   (§13)
      5. Executor appends tasks/completed/ + closes current_task (§10.6)

    §5.4 step 1 (docs/api/schema updates) is author-driven per §7.5 and is not
    Executor-automated. Close-out writes (steps 4–5) run only when the Bridge phase
    completion succeeds and the outcome is `completed`.
    """
    result = CompletionResult(correlation_id=ctx.correlation_id or str(uuid.uuid4()))

    payload: dict[str, object] = {
        "vedaws_task_id": vedaws_task_id,
        "outcome": outcome,
        "human_gate": human_gate,
    }
    if reason:
        payload["reason"] = reason

    phase = orchestrate_phase_complete(paths, ctx, payload)
    result.phase_complete = phase
    result.steps_completed.append("phase_complete")
    result.blockers.extend(phase.blockers)
    result.warnings.extend(phase.warnings)
    result.recovery.extend(phase.recovery)
    if phase.project_state:
        result.project_state = phase.project_state

    # Do not close out if Bridge denied completion or outcome is not a clean close.
    if not phase.ok or outcome != "completed":
        result.blockers = list(dict.fromkeys(result.blockers))
        result.warnings = list(dict.fromkeys(result.warnings))
        result.ok = phase.ok and not result.blockers
        return result

    # §5.4 step 4: HANDOFF refresh (§13).
    facts = handoff_facts or HandoffFacts(what_built=[goal] if goal.strip() else [])
    handoff_path = paths.pos_root / "docs" / "HANDOFF_FOR_DOCUMENTER.md"
    repo = repo_path or str(paths.workspace_root)
    _, handoff_warnings = refresh_handoff(
        handoff_path, facts, repo_path=repo, timestamp=synced_at
    )
    result.handoff_path = str(handoff_path)
    result.handoff_refreshed = True
    result.warnings.extend(handoff_warnings)
    result.steps_completed.append("handoff_refresh")

    # §5.4 step 5 / §10.6: completed log.
    completed_dir = paths.pos_root / "tasks" / "completed"
    log_path, created = write_completed_log(
        completed_dir,
        goal=goal,
        outcome=outcome,
        closed_on=closed_on,
        vedaws_task_id=vedaws_task_id,
        acceptance=acceptance,
        changed_paths=changed_paths,
    )
    result.completed_log_path = log_path
    result.completed_log_created = created
    result.steps_completed.append("completed_log")

    # §10.6 current_task close-out: Status idle + Progress Log entry.
    _, status_changed = set_task_status(paths.current_task_path, "idle")
    result.current_task_closed = status_changed
    append_progress_entry(
        paths.current_task_path,
        changed_paths or [],
        logged_at=closed_on,
        note=f"Phase complete ({outcome}): {goal.strip()}" if goal.strip() else f"Phase complete ({outcome})",
    )
    result.steps_completed.append("current_task_closeout")

    result.blockers = list(dict.fromkeys(result.blockers))
    result.warnings = list(dict.fromkeys(result.warnings))
    result.ok = phase.ok and not result.blockers
    return result
