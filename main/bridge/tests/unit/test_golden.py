"""Golden BridgeResult field keys per operation (§11.5)."""

from __future__ import annotations

from vespawd_bridge.api.types import BridgeResult

REQUIRED_KEYS = {
    "ok",
    "operation",
    "correlation_id",
    "codes",
    "blockers",
    "warnings",
    "vedaws_task_id",
    "project_state",
    "doctor_summary",
    "files_touched",
    "recovery",
    "duration_ms",
    "vedaws_commands_run",
}

OPERATIONS = [
    "bootstrap",
    "ingest_master_prompt",
    "sync_status",
    "pre_implement_check",
    "post_implement",
    "post_phase_complete",
    "pre_documenter",
]


def test_golden_result_shape_all_operations() -> None:
    for operation in OPERATIONS:
        result = BridgeResult(operation=operation, correlation_id="golden", ok=True)
        data = result.to_dict()
        assert REQUIRED_KEYS <= set(data.keys()), operation
        assert data["operation"] == operation
