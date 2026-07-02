"""Public API entry surface (§1.3)."""

from __future__ import annotations

from typing import Any

from vespawd_bridge.api.types import (
    BootstrapInput,
    BridgeContext,
    BridgeResult,
    DocumenterGateInput,
    ImplementGateInput,
    MasterPromptIngest,
    PhaseCompleteInput,
    PostImplementInput,
    SyncInput,
)
from vespawd_bridge.dispatcher.dispatcher import Dispatcher

OPERATIONS = frozenset(
    {
        "bootstrap",
        "ingest_master_prompt",
        "sync_status",
        "pre_implement_check",
        "post_implement",
        "post_phase_complete",
        "pre_documenter",
    }
)

_INPUT_PARSERS = {
    "bootstrap": BootstrapInput.from_dict,
    "ingest_master_prompt": MasterPromptIngest.from_dict,
    "sync_status": SyncInput.from_dict,
    "pre_implement_check": ImplementGateInput.from_dict,
    "post_implement": PostImplementInput.from_dict,
    "post_phase_complete": PhaseCompleteInput.from_dict,
    "pre_documenter": DocumenterGateInput.from_dict,
}

_dispatcher = Dispatcher()


def invoke(operation: str, context: BridgeContext, payload: Any = None) -> BridgeResult:
    """Single public entry for all Bridge operations."""
    if operation not in OPERATIONS:
        result = BridgeResult(operation=operation, correlation_id=context.correlation_id or "")
        result.ok = False
        result.codes.append("internal_error")
        result.blockers.append(f"Unknown operation: {operation}")
        return result

    parser = _INPUT_PARSERS[operation]
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        raise TypeError("payload must be a dict or None")

    parsed = parser(payload)
    return _dispatcher.dispatch(operation, context, parsed)


def invoke_from_dict(
    operation: str, context_data: dict[str, Any], payload: dict[str, Any] | None = None
) -> BridgeResult:
    return invoke(operation, BridgeContext.from_dict(context_data), payload)
