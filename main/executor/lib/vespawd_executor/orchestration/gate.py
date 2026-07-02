"""Pre-implementation gate orchestration (Executor Spec §8.2, §6)."""

from __future__ import annotations

import uuid
from typing import Any

from vespawd_executor.api.types import ExecutorContext
from vespawd_executor.bridge.client import BridgeClient, BridgeResultView
from vespawd_executor.bridge.interpret import (
    extract_recovery_actions,
    should_block_implement,
    summarize_blockers,
)
from vespawd_executor.orchestration.types import GateResult
from vespawd_executor.paths.resolver import WorkspacePaths

_DESIGN_GATE_BLOCKED = "design_gate_blocked"
_DESIGN_GATE_OVERRIDDEN = "design_gate_overridden"
_STATE_INELIGIBLE = "state_ineligible"
_WORKFLOW_TASK_MISMATCH = "workflow_task_mismatch"
_DOCTOR_BLOCKED = "doctor_blocked"


def _bridge_client(paths: WorkspacePaths) -> BridgeClient:
    return BridgeClient(paths.bridge_cli, paths.workspace_root)


def _build_payload(
    current_task: str,
    ctx: ExecutorContext,
) -> dict[str, Any]:
    return {
        "current_task": current_task,
        "skip_design": ctx.session.skip_design,
        "design_later": ctx.session.design_later,
    }


def run_pre_implement_check(
    paths: WorkspacePaths,
    ctx: ExecutorContext,
    current_task: str,
) -> GateResult:
    """
    Invoke the public Bridge `pre_implement_check` and interpret the decision (§8.2).

    Executor never duplicates Bridge validation logic; it only reads the BridgeResult
    and decides whether userspace implementation may proceed.
    """
    result = GateResult(correlation_id=ctx.correlation_id or str(uuid.uuid4()))

    bridge = _bridge_client(paths)
    check = bridge.invoke("pre_implement_check", ctx, _build_payload(current_task, ctx))
    result.check = check

    result.vedaws_task_id = check.vedaws_task_id
    result.project_state = check.project_state
    result.doctor_summary = check.doctor_summary

    codes = set(check.codes)
    result.design_gate_blocked = _DESIGN_GATE_BLOCKED in codes
    result.design_gate_overridden = _DESIGN_GATE_OVERRIDDEN in codes
    result.workflow_ineligible = _STATE_INELIGIBLE in codes
    result.task_mismatch = _WORKFLOW_TASK_MISMATCH in codes
    result.doctor_blocked = _DOCTOR_BLOCKED in codes

    result.warnings = list(dict.fromkeys(check.warnings))
    result.blockers = list(dict.fromkeys(summarize_blockers(check)))
    result.recovery = extract_recovery_actions(check)

    # §8.2 "On failure: do not edit main/src/". Trust Bridge ok plus blocking-code guard.
    result.allow_implement = not should_block_implement(check)
    return result
