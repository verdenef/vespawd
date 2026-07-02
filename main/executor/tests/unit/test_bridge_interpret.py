"""Bridge interpretation tests."""

from __future__ import annotations

from vespawd_executor.bridge.client import BridgeResultView
from vespawd_executor.bridge.interpret import (
    apply_bridge_result,
    extract_recovery_actions,
    is_offline_sync,
    should_block_implement,
    summarize_blockers,
)


def test_offline_sync_not_blocking() -> None:
    result = BridgeResultView(
        ok=True,
        operation="sync_status",
        codes=["orchestration_offline", "vedaws_missing"],
    )
    assert is_offline_sync(result)
    assert summarize_blockers(result) == []
    assert not should_block_implement(result)


def test_state_transition_denied_blocks() -> None:
    result = BridgeResultView(
        ok=False,
        operation="ingest_master_prompt",
        codes=["state_transition_denied"],
        blockers=["transition denied"],
    )
    assert should_block_implement(result)
    assert "state_transition_denied" in summarize_blockers(result)


def test_extract_recovery_actions() -> None:
    result = BridgeResultView(
        ok=False,
        recovery=[
            {
                "code": "state_transition_denied",
                "action": "Check vedaws state",
                "retry_operation": "ingest_master_prompt",
            }
        ],
    )
    actions = extract_recovery_actions(result)
    assert len(actions) == 1
    assert actions[0].retry_operation == "ingest_master_prompt"


def test_apply_bridge_result_sets_block_implement() -> None:
    bridge = BridgeResultView(ok=False, codes=["doctor_blocked"], blockers=["doctor"])
    blockers, warnings, recovery, block = apply_bridge_result(
        blockers=[],
        warnings=[],
        recovery=[],
        bridge=bridge,
        block_implement=False,
    )
    assert block
    assert "doctor_blocked" in blockers
