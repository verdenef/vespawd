"""Post-implementation orchestration (Executor Spec §5.4 steps 2–3)."""

from __future__ import annotations

import uuid
from typing import Any

from vespawd_executor.api.types import ExecutorContext
from vespawd_executor.bridge.client import BridgeClient
from vespawd_executor.bridge.interpret import apply_bridge_result
from vespawd_executor.orchestration.types import CompleteOrchestrationResult
from vespawd_executor.paths.resolver import WorkspacePaths


def orchestrate_phase_complete(
    paths: WorkspacePaths,
    ctx: ExecutorContext,
    payload: dict[str, Any],
) -> CompleteOrchestrationResult:
    """
    §5.4 steps 2–3:
    2. bridge.post_phase_complete
    3. bridge.sync_status
    """
    result = CompleteOrchestrationResult(
        correlation_id=ctx.correlation_id or str(uuid.uuid4()),
    )
    blockers: list[str] = []
    warnings: list[str] = []
    recovery = []

    bridge = BridgeClient(paths.bridge_cli, paths.workspace_root)

    complete = bridge.invoke("post_phase_complete", ctx, payload)
    result.post_phase_complete = complete
    result.steps_completed.append("bridge.post_phase_complete")
    blockers, warnings, recovery, _ = apply_bridge_result(
        blockers=blockers,
        warnings=warnings,
        recovery=recovery,
        bridge=complete,
        block_implement=False,
    )
    if complete.project_state:
        result.project_state = complete.project_state

    sync = bridge.invoke("sync_status", ctx, {})
    result.sync_status = sync
    result.steps_completed.append("bridge.sync_status")
    blockers, warnings, recovery, _ = apply_bridge_result(
        blockers=blockers,
        warnings=warnings,
        recovery=recovery,
        bridge=sync,
        block_implement=False,
    )
    if sync.project_state:
        result.project_state = sync.project_state

    result.blockers = list(dict.fromkeys(blockers))
    result.warnings = list(dict.fromkeys(warnings))
    result.recovery = recovery
    result.ok = complete.ok and not result.blockers
    return result
