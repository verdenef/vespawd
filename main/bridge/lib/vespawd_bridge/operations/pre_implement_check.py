"""pre_implement_check operation (§4.4)."""

from __future__ import annotations

from vespawd_bridge import codes
from vespawd_bridge.api.types import BridgeResult, ImplementGateInput
from vespawd_bridge.cli.parse import parse_doctor, parse_state, parse_workflow_show
from vespawd_bridge.manifest.phase_map import resolve_phase
from vespawd_bridge.operations.context import HandlerContext, apply_validation, truncate_doctor
from vespawd_bridge.projection.engine import enrich_notes
from vespawd_bridge.recovery.engine import hints_for_codes
from vespawd_bridge.validation.engine import (
    validate_design_gate,
    validate_doctor,
    validate_layout,
    validate_manifest_integrity,
    validate_task_alignment,
    validate_workflow_eligibility,
    validate_workflow_corrupt,
)


def handle_pre_implement_check(
    ctx: HandlerContext, payload: ImplementGateInput, correlation_id: str
) -> BridgeResult:
    result = ctx.base_result("pre_implement_check", correlation_id)

    validations = [
        validate_layout(ctx.paths),
        validate_manifest_integrity(ctx.paths),
    ]
    doctor_result = ctx.cli.doctor()
    doctor_snap = parse_doctor(doctor_result.stdout, doctor_result.stderr, doctor_result.exit_code)
    result.doctor_summary = truncate_doctor(
        doctor_snap.doctor_summary, ctx.manifest.doctor_summary_max_chars
    )
    validations.append(
        validate_doctor(doctor_result.exit_code, result.doctor_summary, mode="strict")
    )

    wf = ctx.cli.workflow_show()
    snapshot = parse_workflow_show(wf.stdout, ctx.manifest.workflow_id) if wf.exit_code == 0 else None
    state_result = ctx.cli.state()
    if state_result.exit_code == 0:
        lifecycle = parse_state(state_result.stdout)
        if snapshot is None:
            snapshot = lifecycle
        else:
            snapshot.project_state = lifecycle.project_state

    task_id = ctx.session_overrides.force_phase or (snapshot.active_task_id if snapshot else "")
    validations.append(
        validate_design_gate(
            payload.current_task,
            ctx.paths.design_gate_path,
            skip_design=payload.skip_design or ctx.session_overrides.skip_design,
            design_later=payload.design_later or ctx.session_overrides.design_later,
            ui_keywords=ctx.manifest.ui_keywords,
            vedaws_task_id=task_id,
        )
    )

    if wf.exit_code == 0 and snapshot:
        validations.append(validate_workflow_corrupt(wf.stdout))
        validations.append(validate_workflow_eligibility(snapshot))
        expected_id, _ = resolve_phase(
            payload.current_task,
            None,
            None,
            ctx.manifest.phase_map,
            force_phase=ctx.session_overrides.force_phase,
        )
        validations.append(
            validate_task_alignment(payload.current_task, snapshot, expected_id)
        )
        result.project_state = snapshot.project_state
        result.vedaws_task_id = snapshot.active_task_id or expected_id

    for validation in validations:
        apply_validation(result, validation)

    blocking = [c for c in result.codes if c in codes.BLOCKING_CODES]
    result.ok = len(blocking) == 0
    if result.ok:
        result.codes.append(codes.OK)
    else:
        note_rel, _ = enrich_notes(
            ctx.paths,
            vedaws_task_id=result.vedaws_task_id or "unknown",
            project_state=result.project_state or "unknown",
            blockers=result.blockers,
        )
        if note_rel:
            result.files_touched.append(note_rel)
            ctx.logger.projection_write(result.files_touched)
        result.recovery = hints_for_codes(result.codes)
    return result
