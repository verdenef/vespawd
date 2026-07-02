"""Bridge result interpretation and recovery (Executor Spec §8, §11.5)."""

from __future__ import annotations

from vespawd_executor.bridge.client import BridgeResultView
from vespawd_executor.orchestration.types import RecoveryAction

BLOCKING_BRIDGE_CODES = frozenset(
    {
        "doctor_blocked",
        "design_gate_blocked",
        "state_ineligible",
        "state_transition_denied",
        "bootstrap_failed",
        "layout_conflict",
        "vedaws_missing",
        "task_complete_denied",
        "artifacts_missing",
        "workflow_corrupt",
        "invalid_manifest",
        "missing_manifest",
        "invalid_path",
        "version_mismatch",
        "cli_failed",
        "cli_timeout",
        "cli_spawn_error",
        "internal_error",
    }
)

EXECUTOR_BRIDGE_FAILURE_CODES = frozenset(
    {
        "bridge_missing",
        "bridge_invoke_failed",
    }
)

WARNING_BRIDGE_CODES = frozenset(
    {
        "orchestration_offline",
        "workflow_task_mismatch",
        "phase_map_miss",
        "sync_incomplete",
        "handoff_stale",
        "doctor_warn",
    }
)


def extract_recovery_actions(result: BridgeResultView) -> list[RecoveryAction]:
    actions: list[RecoveryAction] = []
    for item in result.recovery:
        if isinstance(item, dict) and item.get("action"):
            actions.append(RecoveryAction.from_dict(item))
    return actions


def summarize_blockers(result: BridgeResultView) -> list[str]:
    if result.operation == "sync_status" and result.ok and is_offline_sync(result):
        return list(result.blockers)
    blockers = list(result.blockers)
    for code in result.codes:
        if code in BLOCKING_BRIDGE_CODES and code not in blockers:
            blockers.append(code)
    for code in result.codes:
        if code in EXECUTOR_BRIDGE_FAILURE_CODES and code not in blockers:
            blockers.append(code)
    return blockers


def should_block_implement(result: BridgeResultView) -> bool:
    if result.operation == "sync_status" and result.ok and is_offline_sync(result):
        return False
    if not result.ok:
        return True
    return any(code in BLOCKING_BRIDGE_CODES for code in result.codes)


def is_offline_sync(result: BridgeResultView) -> bool:
    return "orchestration_offline" in result.codes or "vedaws_missing" in result.codes


def merge_bridge_into_startup(
    startup_blockers: list[str],
    startup_warnings: list[str],
    bridge: BridgeResultView,
) -> tuple[list[str], list[str], bool]:
    blockers = list(startup_blockers)
    warnings = list(startup_warnings)
    warnings.extend(bridge.warnings)
    bridge_blockers = summarize_blockers(bridge)
    if bridge_blockers:
        blockers.extend(bridge_blockers)
    ok = bridge.ok and not blockers
    if is_offline_sync(bridge) and not bridge_blockers:
        ok = True
    return blockers, warnings, ok


def apply_bridge_result(
    *,
    blockers: list[str],
    warnings: list[str],
    recovery: list[RecoveryAction],
    bridge: BridgeResultView,
    block_implement: bool,
) -> tuple[list[str], list[str], list[RecoveryAction], bool]:
    warnings = list(warnings)
    blockers = list(blockers)
    recovery = list(recovery)
    warnings.extend(bridge.warnings)
    bridge_blockers = summarize_blockers(bridge)
    if bridge_blockers:
        blockers.extend(bridge_blockers)
    recovery.extend(extract_recovery_actions(bridge))
    if block_implement and should_block_implement(bridge):
        block_implement = True
    elif bridge_blockers:
        block_implement = True
    return blockers, warnings, recovery, block_implement
