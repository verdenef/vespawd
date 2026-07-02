"""Post-implementation orchestration (Executor Spec §7 guard + §8.3 hooks)."""

from __future__ import annotations

import uuid
from datetime import date

from vespawd_executor.api.types import ExecutorContext
from vespawd_executor.bridge.client import BridgeClient
from vespawd_executor.bridge.interpret import (
    apply_bridge_result,
    extract_recovery_actions,
    summarize_blockers,
)
from vespawd_executor.orchestration.types import PostImplementResult
from vespawd_executor.paths.resolver import WorkspacePaths
from vespawd_executor.policy.userspace import check_changed_paths
from vespawd_executor.sync.progress_log import append_progress_entry


def _normalize(changed_paths: list[str]) -> list[str]:
    seen: list[str] = []
    for raw in changed_paths:
        if not raw or not str(raw).strip():
            continue
        value = str(raw).strip().replace("\\", "/")
        if value not in seen:
            seen.append(value)
    return seen


def orchestrate_post_implement(
    paths: WorkspacePaths,
    ctx: ExecutorContext,
    changed_paths: list[str],
    *,
    vedaws_task_id: str = "",
    logged_at: date | None = None,
    note: str | None = None,
) -> PostImplementResult:
    """
    §7 policy guard, then §8.3 after-implementation hooks:
    1. Record files-changed summary in current_task.md Progress Log.
    2. bridge.post_implement (optional telemetry per §8.1).
    3. bridge.sync_status.

    Forbidden edits (§7.2) block the sequence before Progress Log / Bridge hooks.
    `post_implement` is telemetry: non-strict Bridge worker failures surface as
    warnings (Bridge ok=True), while strict failures propagate as blockers.
    """
    result = PostImplementResult(correlation_id=ctx.correlation_id or str(uuid.uuid4()))
    normalized = _normalize(changed_paths)

    # §7.1 / §7.2 policy guard (read-only).
    report = check_changed_paths(paths, normalized)
    result.policy = report
    result.warnings.extend(report.warnings())
    if report.has_violations:
        result.blockers.extend(report.blockers())
        result.ok = False
        return result

    # §8.3 step 1: Progress Log.
    _, appended = append_progress_entry(
        paths.current_task_path, normalized, logged_at=logged_at, note=note
    )
    result.progress_logged = appended
    result.progress_path = str(paths.current_task_path)
    result.steps_completed.append("progress_log")

    bridge = BridgeClient(paths.bridge_cli, paths.workspace_root)

    # §8.3 step 2: bridge.post_implement (ok-authoritative interpretation).
    payload = {"vedaws_task_id": vedaws_task_id or "", "changed_paths": normalized}
    post = bridge.invoke("post_implement", ctx, payload)
    result.post_implement = post
    result.steps_completed.append("bridge.post_implement")
    result.warnings.extend(post.warnings)
    result.recovery.extend(extract_recovery_actions(post))
    if not post.ok:
        result.blockers.extend(summarize_blockers(post))
    if post.vedaws_task_id:
        result.vedaws_task_id = post.vedaws_task_id
    if post.project_state:
        result.project_state = post.project_state

    # §8.1: sync_status after major steps.
    sync = bridge.invoke("sync_status", ctx, {})
    result.sync_status = sync
    result.steps_completed.append("bridge.sync_status")
    result.blockers, result.warnings, result.recovery, _ = apply_bridge_result(
        blockers=result.blockers,
        warnings=result.warnings,
        recovery=result.recovery,
        bridge=sync,
        block_implement=False,
    )
    if sync.project_state:
        result.project_state = sync.project_state

    result.blockers = list(dict.fromkeys(result.blockers))
    result.warnings = list(dict.fromkeys(result.warnings))
    result.ok = post.ok and not result.blockers
    return result
