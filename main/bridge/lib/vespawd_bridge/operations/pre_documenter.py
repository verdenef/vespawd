"""pre_documenter operation (§4.7)."""

from __future__ import annotations

from vespawd_bridge import codes
from vespawd_bridge.api.types import BridgeResult, DocumenterGateInput
from vespawd_bridge.cli.parse import parse_artifacts, parse_doctor
from vespawd_bridge.operations.context import HandlerContext, apply_validation, truncate_doctor
from vespawd_bridge.operations.sync_status import handle_sync_status
from vespawd_bridge.projection.engine import mirror_handoff, read_handoff_freshness
from vespawd_bridge.recovery.engine import hints_for_codes
from vespawd_bridge.validation.engine import validate_artifacts, validate_doctor


def handle_pre_documenter(
    ctx: HandlerContext, payload: DocumenterGateInput, correlation_id: str
) -> BridgeResult:
    result = ctx.base_result("pre_documenter", correlation_id)

    doctor_result = ctx.cli.doctor()
    doctor_snap = parse_doctor(doctor_result.stdout, doctor_result.stderr, doctor_result.exit_code)
    result.doctor_summary = truncate_doctor(
        doctor_snap.doctor_summary, ctx.manifest.doctor_summary_max_chars
    )
    doctor_val = validate_doctor(doctor_result.exit_code, result.doctor_summary, mode="strict")
    apply_validation(result, doctor_val)

    art_result = ctx.cli.software_artifacts()
    art_snap = parse_artifacts(art_result.stdout, art_result.stderr, art_result.exit_code)
    art_val = validate_artifacts(art_snap.artifacts_report, art_result.exit_code)
    apply_validation(result, art_val)

    handoff_state, handoff_warnings = read_handoff_freshness(ctx.paths.handoff_path)
    result.warnings.extend(handoff_warnings)
    if handoff_state == "stale":
        result.codes.append(codes.HANDOFF_STALE)

    if art_val.passed and doctor_val.passed:
        complete = ctx.cli.tasks_complete("software.handoff")
        if complete.exit_code != 0:
            result.warnings.append("software.handoff completion skipped")

    if ctx.manifest.handoff_mirror:
        mirrored = mirror_handoff(ctx.paths, ctx.manifest.handoff_mirror)
        if mirrored:
            result.files_touched.append(mirrored)

    sync = handle_sync_status(ctx, correlation_id)
    result.files_touched.extend(sync.files_touched)
    result.project_state = sync.project_state
    result.warnings.extend(sync.warnings)

    blocking = [c for c in result.codes if c in codes.BLOCKING_CODES]
    result.ok = len(blocking) == 0
    if result.ok:
        result.codes.append(codes.OK)
    else:
        result.recovery = hints_for_codes(result.codes)
    return result
