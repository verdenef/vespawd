"""sync_status operation (§4.3)."""

from __future__ import annotations

import re

from vespawd_bridge import codes
from vespawd_bridge.api.types import BridgeResult, SyncInput
from vespawd_bridge.cli.parse import VedawsSnapshot
from vespawd_bridge.operations.context import HandlerContext, truncate_doctor
from vespawd_bridge.projection.engine import enrich_notes, write_status
from vespawd_bridge.recovery.engine import hints_for_codes


def _read_prior_phase(status_path) -> str | None:
    if not status_path.is_file():
        return None
    text = status_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^\|\s*Phase\s*\|\s*([^|]+)\|", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def handle_sync_status(
    ctx: HandlerContext,
    correlation_id: str,
    payload: SyncInput | None = None,
) -> BridgeResult:
    result = ctx.base_result("sync_status", correlation_id)
    prior_phase = _read_prior_phase(ctx.paths.status_path)

    if not ctx.vedaws_available:
        rel, warnings = write_status(
            ctx.paths,
            VedawsSnapshot(),
            offline=True,
            prior_phase=prior_phase,
            skip_design=ctx.session_overrides.skip_design,
        )
        result.files_touched.append(rel)
        ctx.logger.projection_write(result.files_touched)
        result.warnings.extend(warnings)
        result.codes.append(codes.ORCHESTRATION_OFFLINE)
        result.codes.append(codes.VEDAWS_MISSING)
        result.warnings.append("Vedaws unavailable; wrote offline status projection")
        result.ok = True
        result.project_state = "offline"
        return result

    snapshot, issues = ctx.cli.build_snapshot()
    if issues:
        result.codes.extend(issues)
        if issues:
            result.warnings.append(codes.SYNC_INCOMPLETE)

    rel, warnings = write_status(
        ctx.paths,
        snapshot,
        offline=False,
        prior_phase=prior_phase if issues else None,
        skip_design=ctx.session_overrides.skip_design,
    )
    result.files_touched.append(rel)
    result.warnings.extend(warnings)
    result.project_state = snapshot.project_state
    result.vedaws_task_id = snapshot.active_task_id

    note_rel, note_warnings = enrich_notes(
        ctx.paths,
        vedaws_task_id=snapshot.active_task_id or "unknown",
        project_state=snapshot.project_state or "unknown",
    )
    if note_rel:
        result.files_touched.append(note_rel)
    result.warnings.extend(note_warnings)
    if result.files_touched:
        ctx.logger.projection_write(result.files_touched)

    result.ok = True
    if not issues:
        result.codes.append(codes.OK)
    else:
        result.recovery = hints_for_codes([codes.SYNC_INCOMPLETE])
    return result
