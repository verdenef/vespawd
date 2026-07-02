"""Recovery recommendations (§9.2, §9.3)."""

from __future__ import annotations

from vespawd_bridge import codes
from vespawd_bridge.api.types import RecoveryHint

RECOVERY_MAP: dict[str, RecoveryHint] = {
    codes.VEDAWS_MISSING: RecoveryHint(
        code=codes.VEDAWS_MISSING,
        action="Install Vedaws; continue in PAWS-only degraded mode",
        retry_operation="sync_status",
    ),
    codes.MISSING_MANIFEST: RecoveryHint(
        code=codes.MISSING_MANIFEST,
        action="Restore main/bridge/manifest.toml",
        retry_operation="bootstrap",
    ),
    codes.BOOTSTRAP_FAILED: RecoveryHint(
        code=codes.BOOTSTRAP_FAILED,
        action="Check logs; run bootstrap after fixing environment",
        retry_operation="bootstrap",
    ),
    codes.DOCTOR_BLOCKED: RecoveryHint(
        code=codes.DOCTOR_BLOCKED,
        action="Run vedaws doctor manually; fix environment issues",
        retry_operation="pre_implement_check",
    ),
    codes.DESIGN_GATE_BLOCKED: RecoveryHint(
        code=codes.DESIGN_GATE_BLOCKED,
        action="Complete DESIGN.md or pass skip_design in session_overrides",
        retry_operation="pre_implement_check",
    ),
    codes.SYNC_INCOMPLETE: RecoveryHint(
        code=codes.SYNC_INCOMPLETE,
        action="Retry sync_status",
        retry_operation="sync_status",
    ),
    codes.WORKFLOW_CORRUPT: RecoveryHint(
        code=codes.WORKFLOW_CORRUPT,
        action="Follow Bridge Spec recovery; requires human approval for destructive steps",
        retry_operation="bootstrap",
        destructive=True,
    ),
    codes.TASK_COMPLETE_DENIED: RecoveryHint(
        code=codes.TASK_COMPLETE_DENIED,
        action="Run vedaws workflow show; fix task dependencies",
        retry_operation="post_phase_complete",
    ),
    codes.ARTIFACTS_MISSING: RecoveryHint(
        code=codes.ARTIFACTS_MISSING,
        action="Executor updates docs; retry pre_documenter",
        retry_operation="pre_documenter",
    ),
    codes.CLI_TIMEOUT: RecoveryHint(
        code=codes.CLI_TIMEOUT,
        action="Retry the operation; check Vedaws responsiveness",
    ),
    codes.CLI_SPAWN_ERROR: RecoveryHint(
        code=codes.CLI_SPAWN_ERROR,
        action="Verify vedaws CLI path in manifest",
        retry_operation="bootstrap",
    ),
}


def hints_for_codes(code_list: list[str]) -> list[RecoveryHint]:
    hints: list[RecoveryHint] = []
    seen: set[str] = set()
    for code in code_list:
        if code in seen:
            continue
        seen.add(code)
        hint = RECOVERY_MAP.get(code)
        if hint:
            hints.append(hint)
    return hints


class RecoveryTracker:
    """Prevent duplicate post_phase_complete retries per correlation_id (§9.3)."""

    _completed_retries: dict[str, set[str]] = {}

    def can_retry_phase_complete(self, correlation_id: str, task_id: str) -> bool:
        key = f"{correlation_id}:{task_id}"
        attempts = self._completed_retries.setdefault(correlation_id, set())
        if task_id in attempts:
            return False
        attempts.add(task_id)
        return True
