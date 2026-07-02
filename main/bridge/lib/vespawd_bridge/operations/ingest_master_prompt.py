"""ingest_master_prompt operation (§4.2)."""

from __future__ import annotations

from vespawd_bridge import codes
from vespawd_bridge.api.types import BootstrapInput, BridgeResult, MasterPromptIngest
from vespawd_bridge.cli.parse import parse_state, parse_status_output, parse_workflow_show
from vespawd_bridge.manifest.phase_map import resolve_phase
from vespawd_bridge.operations.bootstrap import handle_bootstrap
from vespawd_bridge.operations.context import HandlerContext
from vespawd_bridge.operations.sync_status import handle_sync_status
from vespawd_bridge.projection.engine import enrich_notes
from vespawd_bridge.recovery.engine import hints_for_codes

_EXECUTING_PHASES = frozenset({"implement", "test", "review", "handoff"})
# Vedaws has no direct awaiting_approval → planning edge; use executing → ready → planning.
_APPROVAL_RELEASE_PATH = ("executing", "ready", "planning")


def _ingest_state_transitions(ctx: HandlerContext, task_id: str, project_state: str) -> str | None:
    """Apply planning/ready/executing transitions per Bridge Spec §7.6 and Vedaws state machine."""
    state = (project_state or "").lower()
    task_key = task_id.removeprefix("software.")
    want_executing = task_key in _EXECUTING_PHASES

    if state == "awaiting_approval":
        for target in _APPROVAL_RELEASE_PATH:
            step = ctx.cli.state_transition(target)
            if step.exit_code != 0:
                return step.stderr or "state transition denied"
        state = "planning"

    if state in {"", "created", "initialized"}:
        planning = ctx.cli.state_transition("planning")
        if planning.exit_code != 0:
            return planning.stderr or "state transition denied"
        state = "planning"

    if want_executing:
        if state == "planning":
            ready = ctx.cli.state_transition("ready")
            if ready.exit_code != 0:
                return ready.stderr or "state transition denied"
            state = "ready"
        if state == "ready":
            executing = ctx.cli.state_transition("executing")
            if executing.exit_code != 0:
                return executing.stderr or "state transition denied"

    return None


def handle_ingest_master_prompt(
    ctx: HandlerContext, payload: MasterPromptIngest, correlation_id: str
) -> BridgeResult:
    result = ctx.base_result("ingest_master_prompt", correlation_id)

    vedaws_marker = ctx.paths.vedaws_project_root / ".vedaws" / "project.toml"
    if not vedaws_marker.is_file():
        boot = handle_bootstrap(
            ctx, BootstrapInput(project_name=payload.project_context_product_name), correlation_id
        )
        if not boot.ok:
            return boot

    task_id, used_fallback = resolve_phase(
        payload.current_task_goal,
        payload.current_task_notes,
        payload.phase_hint,
        ctx.manifest.phase_map,
        force_phase=ctx.session_overrides.force_phase,
    )
    result.vedaws_task_id = task_id
    if used_fallback:
        result.codes.append(codes.PHASE_MAP_MISS)
        result.warnings.append(f"Phase mapped via fallback to {task_id}")

    wf = ctx.cli.workflow_show()
    if wf.exit_code == 0:
        wf_snap = parse_workflow_show(wf.stdout, ctx.manifest.workflow_id)
        if wf_snap.active_task_id and not used_fallback:
            if wf_snap.active_task_id != task_id:
                result.codes.append(codes.WORKFLOW_TASK_MISMATCH)
                result.warnings.append(
                    f"Vedaws active task {wf_snap.active_task_id} differs from mapped {task_id}"
                )

    status = ctx.cli.status()
    if status.exit_code == 0:
        snap = parse_status_output(status.stdout)
        result.project_state = snap.project_state

    state_result = ctx.cli.state()
    if state_result.exit_code == 0:
        lifecycle = parse_state(state_result.stdout)
        if lifecycle.project_state:
            result.project_state = lifecycle.project_state

    transition_error = _ingest_state_transitions(ctx, task_id, result.project_state)
    if transition_error:
        result.ok = False
        result.codes.append(codes.STATE_TRANSITION_DENIED)
        result.blockers.append(transition_error)
        result.recovery = hints_for_codes(result.codes)
        return result

    if state_result.exit_code == 0:
        lifecycle = parse_state(state_result.stdout)
        if lifecycle.project_state:
            result.project_state = lifecycle.project_state

    note_rel, note_warnings = enrich_notes(
        ctx.paths,
        vedaws_task_id=task_id,
        project_state=result.project_state or "unknown",
    )
    if note_rel:
        result.files_touched.append(note_rel)
    result.warnings.extend(note_warnings)

    sync = handle_sync_status(ctx, correlation_id)
    result.files_touched.extend(sync.files_touched)
    result.warnings.extend(sync.warnings)
    result.codes.extend([c for c in sync.codes if c not in result.codes])
    result.project_state = sync.project_state or result.project_state

    blocking = [c for c in result.codes if c in codes.BLOCKING_CODES]
    result.ok = not blocking
    if result.ok:
        if codes.OK not in result.codes:
            result.codes.append(codes.OK)
    else:
        result.recovery = hints_for_codes(result.codes)
    return result
