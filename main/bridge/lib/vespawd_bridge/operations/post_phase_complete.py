"""post_phase_complete operation (§4.6)."""

from __future__ import annotations

from vespawd_bridge import codes
from vespawd_bridge.api.types import BridgeResult, PhaseCompleteInput
from vespawd_bridge.operations.context import HandlerContext
from vespawd_bridge.operations.sync_status import handle_sync_status
from vespawd_bridge.validation.engine import validate_task_exists
from vespawd_bridge.cli.parse import parse_workflow_show
from vespawd_bridge.recovery.engine import hints_for_codes


def handle_post_phase_complete(
    ctx: HandlerContext, payload: PhaseCompleteInput, correlation_id: str
) -> BridgeResult:
    result = ctx.base_result("post_phase_complete", correlation_id)
    result.vedaws_task_id = payload.vedaws_task_id

    wf = ctx.cli.workflow_show()
    if wf.exit_code == 0:
        snapshot = parse_workflow_show(wf.stdout, ctx.manifest.workflow_id)
        task_val = validate_task_exists(snapshot, payload.vedaws_task_id)
        if not task_val.passed:
            result.ok = False
            result.codes.extend(task_val.codes)
            result.blockers.extend(task_val.messages)
            result.recovery = hints_for_codes(result.codes)
            return result

    if payload.outcome == "completed":
        if ctx.recovery_tracker and not ctx.recovery_tracker.can_retry_phase_complete(
            correlation_id, payload.vedaws_task_id
        ):
            result.warnings.append("post_phase_complete already attempted for this correlation_id")
        complete = ctx.cli.tasks_complete(payload.vedaws_task_id)
        if complete.exit_code != 0:
            result.ok = False
            result.codes.append(codes.TASK_COMPLETE_DENIED)
            result.blockers.append(complete.stderr or "tasks complete rejected")
            result.recovery = hints_for_codes(result.codes)
            return result
    elif payload.outcome == "failed":
        fail = ctx.cli.tasks_fail(payload.vedaws_task_id)
        if fail.exit_code != 0:
            result.warnings.append("tasks fail unavailable or rejected")

    run_result = ctx.cli.run_dispatch()
    if run_result.exit_code != 0:
        result.warnings.append("automation run after phase complete reported issues")

    if payload.human_gate:
        transition = ctx.cli.state_transition("awaiting_approval")
        if transition.exit_code != 0:
            result.warnings.append("awaiting_approval transition skipped")

    sync = handle_sync_status(ctx, correlation_id)
    result.files_touched.extend(sync.files_touched)
    result.project_state = sync.project_state
    result.warnings.extend(sync.warnings)
    result.codes.extend([c for c in sync.codes if c not in result.codes])

    result.ok = True
    result.codes.append(codes.OK)
    return result
