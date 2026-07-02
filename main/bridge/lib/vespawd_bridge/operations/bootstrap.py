"""bootstrap operation (§4.1)."""

from __future__ import annotations

from pathlib import Path

from vespawd_bridge import codes
from vespawd_bridge.api.types import BootstrapInput, BridgeResult
from vespawd_bridge.cli.parse import parse_doctor, parse_workflow_show
from vespawd_bridge.operations.context import HandlerContext, apply_validation, truncate_doctor
from vespawd_bridge.operations.sync_status import handle_sync_status
from vespawd_bridge.recovery.engine import hints_for_codes
from vespawd_bridge.validation.engine import validate_doctor, validate_layout, validate_manifest_integrity, validate_version


def handle_bootstrap(ctx: HandlerContext, payload: BootstrapInput, correlation_id: str) -> BridgeResult:
    result = ctx.base_result("bootstrap", correlation_id)

    layout_val = validate_layout(ctx.paths)
    apply_validation(result, layout_val)
    version_val = validate_version(ctx.manifest, ctx.implementation_version)
    apply_validation(result, version_val)
    if not version_val.passed:
        result.ok = False
        result.recovery = hints_for_codes(result.codes)
        return result

    vedaws_marker = ctx.paths.vedaws_project_root / ".vedaws" / "project.toml"
    if not vedaws_marker.is_file():
        name = payload.project_name
        if not name and ctx.paths.project_context_path.is_file():
            import re

            text = ctx.paths.project_context_path.read_text(encoding="utf-8", errors="replace")
            match = re.search(r"\*\*Name:\*\*\s*(\S+)", text)
            if match:
                name = match.group(1)
        init_result = ctx.cli.init_software_template(name)
        if init_result.exit_code != 0:
            result.ok = False
            result.codes.append(codes.BOOTSTRAP_FAILED)
            result.blockers.append(init_result.stderr or "vedaws init failed")
            result.recovery = hints_for_codes(result.codes)
            return result

    wf_show = ctx.cli.workflow_show()
    if wf_show.exit_code == 0:
        wf_snap = parse_workflow_show(wf_show.stdout, ctx.manifest.workflow_id)
        if wf_snap.project_state in {"defined", ""} or "defined" in wf_show.stdout.lower():
            activate = ctx.cli.workflow_activate()
            if activate.exit_code != 0:
                result.warnings.append(activate.stderr or "workflow activate warning")

    doctor_result = ctx.cli.doctor()
    doctor_snap = parse_doctor(doctor_result.stdout, doctor_result.stderr, doctor_result.exit_code)
    result.doctor_summary = truncate_doctor(
        doctor_snap.doctor_summary, ctx.manifest.doctor_summary_max_chars
    )
    doctor_val = validate_doctor(doctor_result.exit_code, result.doctor_summary, mode="strict")
    apply_validation(result, doctor_val)

    if doctor_result.exit_code == 0:
        state_result = ctx.cli.state()
        if state_result.exit_code == 0 and "created" in state_result.stdout.lower():
            transition = ctx.cli.state_transition("initialized")
            if transition.exit_code != 0:
                result.warnings.append("state transition to initialized skipped")

    sync_result = handle_sync_status(ctx, correlation_id)
    result.files_touched.extend(sync_result.files_touched)
    if result.files_touched:
        ctx.logger.projection_write(result.files_touched)
    result.warnings.extend(sync_result.warnings)
    result.codes.extend([c for c in sync_result.codes if c not in result.codes])
    result.project_state = sync_result.project_state
    result.vedaws_task_id = sync_result.vedaws_task_id

    integrity = validate_manifest_integrity(ctx.paths)
    apply_validation(result, integrity)

    blocking = [c for c in result.codes if c in codes.BLOCKING_CODES]
    result.ok = not blocking and doctor_val.passed
    if not result.ok:
        result.recovery = hints_for_codes(result.codes)
    else:
        result.codes.append(codes.OK)
    return result
