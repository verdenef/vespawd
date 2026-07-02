"""Pre-documenter gate orchestration (Executor Spec §8.5)."""

from __future__ import annotations

import uuid

from vespawd_executor.api.types import ExecutorContext
from vespawd_executor.bridge.client import BridgeClient
from vespawd_executor.bridge.interpret import (
    extract_recovery_actions,
    should_block_implement,
    summarize_blockers,
)
from vespawd_executor.orchestration.types import DocumenterResult
from vespawd_executor.paths.resolver import WorkspacePaths

_ARTIFACTS_MISSING = "artifacts_missing"
_HANDOFF_STALE = "handoff_stale"
_DOCTOR_BLOCKED = "doctor_blocked"


def orchestrate_pre_documenter(
    paths: WorkspacePaths,
    ctx: ExecutorContext,
) -> DocumenterResult:
    """
    Invoke the public Bridge `pre_documenter` (§8.5).

    Bridge runs `software artifacts`, checks HANDOFF freshness, marks the handoff
    workflow task complete when eligible, and syncs status. Executor only interprets
    the BridgeResult; it never duplicates artifact/doctor validation.
    """
    result = DocumenterResult(correlation_id=ctx.correlation_id or str(uuid.uuid4()))

    bridge = BridgeClient(paths.bridge_cli, paths.workspace_root)
    check = bridge.invoke("pre_documenter", ctx, {})
    result.check = check

    result.project_state = check.project_state
    result.doctor_summary = check.doctor_summary
    result.files_touched = list(check.files_touched)

    codes = set(check.codes)
    result.artifacts_missing = _ARTIFACTS_MISSING in codes
    result.handoff_stale = _HANDOFF_STALE in codes
    result.doctor_blocked = _DOCTOR_BLOCKED in codes

    result.warnings = list(dict.fromkeys(check.warnings))
    result.blockers = list(dict.fromkeys(summarize_blockers(check)))
    result.recovery = extract_recovery_actions(check)

    result.ok = not should_block_implement(check)
    # Handoff-ready (§13.5): gate passed and HANDOFF not stale.
    result.handoff_ready = result.ok and not result.handoff_stale
    return result
