"""Phase complete orchestration unit tests (§5.4)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from vespawd_executor.api.types import ExecutorContext
from vespawd_executor.bridge.client import BridgeResultView
from vespawd_executor.orchestration.complete import orchestrate_phase_complete
from vespawd_executor.paths.resolver import resolve_workspace_paths


@patch("vespawd_executor.orchestration.complete.BridgeClient")
def test_complete_sequence_order(mock_client_cls, fixture_workspace) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.invoke.side_effect = [
        BridgeResultView(ok=True, operation="post_phase_complete", codes=["ok"]),
        BridgeResultView(
            ok=True,
            operation="sync_status",
            codes=["ok"],
            project_state="awaiting_approval",
        ),
    ]

    paths = resolve_workspace_paths(fixture_workspace)
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = orchestrate_phase_complete(
        paths,
        ctx,
        {
            "vedaws_task_id": "software.scope",
            "outcome": "completed",
            "human_gate": True,
        },
    )

    assert result.ok
    assert result.steps_completed == [
        "bridge.post_phase_complete",
        "bridge.sync_status",
    ]
    assert mock_client.invoke.call_args_list[0].args[0] == "post_phase_complete"
    assert mock_client.invoke.call_args_list[1].args[0] == "sync_status"


@patch("vespawd_executor.orchestration.complete.BridgeClient")
def test_complete_task_denied(mock_client_cls, fixture_workspace) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.invoke.side_effect = [
        BridgeResultView(
            ok=False,
            operation="post_phase_complete",
            codes=["task_complete_denied"],
            blockers=["complete rejected"],
        ),
        BridgeResultView(ok=True, operation="sync_status", codes=["ok"]),
    ]

    paths = resolve_workspace_paths(fixture_workspace)
    result = orchestrate_phase_complete(
        paths,
        ExecutorContext(workspace_root=str(fixture_workspace)),
        {"vedaws_task_id": "software.scope", "outcome": "completed"},
    )
    assert not result.ok
    assert "task_complete_denied" in result.blockers
    assert mock_client.invoke.call_count == 2
