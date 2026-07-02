"""pre_implement_check gate unit tests (§8.2)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from vespawd_executor.api.types import ExecutorContext, SessionOptions
from vespawd_executor.bridge.client import BridgeResultView
from vespawd_executor.orchestration.gate import run_pre_implement_check
from vespawd_executor.paths.resolver import resolve_workspace_paths


def _paths(fixture_workspace):
    return resolve_workspace_paths(fixture_workspace)


@patch("vespawd_executor.orchestration.gate.BridgeClient")
def test_gate_allows_when_ok(mock_client_cls, fixture_workspace) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.invoke.return_value = BridgeResultView(
        ok=True,
        operation="pre_implement_check",
        codes=["ok"],
        vedaws_task_id="software.implement",
        project_state="executing",
    )
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = run_pre_implement_check(_paths(fixture_workspace), ctx, "Implement backend")
    assert result.allow_implement
    assert not result.blockers
    assert result.vedaws_task_id == "software.implement"
    assert mock_client.invoke.call_args.args[0] == "pre_implement_check"


@patch("vespawd_executor.orchestration.gate.BridgeClient")
def test_gate_blocks_on_design_gate(mock_client_cls, fixture_workspace) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.invoke.return_value = BridgeResultView(
        ok=False,
        operation="pre_implement_check",
        codes=["design_gate_blocked"],
        blockers=["design gate: DESIGN.md not ready"],
        recovery=[{"code": "design_gate_blocked", "action": "Update design/DESIGN.md"}],
    )
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = run_pre_implement_check(_paths(fixture_workspace), ctx, "Build dashboard UI")
    assert not result.allow_implement
    assert result.design_gate_blocked
    assert "design_gate_blocked" in result.blockers
    assert result.recovery and result.recovery[0].action


@patch("vespawd_executor.orchestration.gate.BridgeClient")
def test_gate_blocks_on_workflow_ineligible(mock_client_cls, fixture_workspace) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.invoke.return_value = BridgeResultView(
        ok=False,
        operation="pre_implement_check",
        codes=["state_ineligible"],
        blockers=["state awaiting_approval not eligible"],
    )
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = run_pre_implement_check(_paths(fixture_workspace), ctx, "Implement")
    assert not result.allow_implement
    assert result.workflow_ineligible


@patch("vespawd_executor.orchestration.gate.BridgeClient")
def test_gate_task_mismatch_is_warning(mock_client_cls, fixture_workspace) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.invoke.return_value = BridgeResultView(
        ok=True,
        operation="pre_implement_check",
        codes=["ok", "workflow_task_mismatch"],
        warnings=["PAWS task drift"],
    )
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = run_pre_implement_check(_paths(fixture_workspace), ctx, "Implement")
    assert result.allow_implement
    assert result.task_mismatch
    assert any("drift" in w.lower() for w in result.warnings)


@patch("vespawd_executor.orchestration.gate.BridgeClient")
def test_gate_design_override_allows(mock_client_cls, fixture_workspace) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.invoke.return_value = BridgeResultView(
        ok=True,
        operation="pre_implement_check",
        codes=["ok", "design_gate_overridden"],
        warnings=["design gate overridden by session"],
    )
    ctx = ExecutorContext(
        workspace_root=str(fixture_workspace),
        session=SessionOptions(skip_design=True),
    )
    result = run_pre_implement_check(_paths(fixture_workspace), ctx, "Build UI")
    assert result.allow_implement
    assert result.design_gate_overridden
    payload = mock_client.invoke.call_args.args[2]
    assert payload["skip_design"] is True


@patch("vespawd_executor.orchestration.gate.BridgeClient")
def test_gate_blocks_on_bridge_failure(mock_client_cls, fixture_workspace) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.invoke.return_value = BridgeResultView(
        ok=False,
        operation="pre_implement_check",
        codes=["bridge_invoke_failed"],
        blockers=["Bridge invoke produced no result"],
    )
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = run_pre_implement_check(_paths(fixture_workspace), ctx, "Implement")
    assert not result.allow_implement
    assert result.blockers


@patch("vespawd_executor.orchestration.gate.BridgeClient")
def test_gate_doctor_blocked(mock_client_cls, fixture_workspace) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.invoke.return_value = BridgeResultView(
        ok=False,
        operation="pre_implement_check",
        codes=["doctor_blocked"],
        blockers=["doctor failed"],
        doctor_summary="1 hard failure",
    )
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = run_pre_implement_check(_paths(fixture_workspace), ctx, "Implement")
    assert not result.allow_implement
    assert result.doctor_blocked
    assert result.doctor_summary


@patch("vespawd_executor.orchestration.gate.BridgeClient")
def test_gate_idempotent_repeated(mock_client_cls, fixture_workspace) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.invoke.return_value = BridgeResultView(
        ok=True,
        operation="pre_implement_check",
        codes=["ok"],
    )
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    paths = _paths(fixture_workspace)
    first = run_pre_implement_check(paths, ctx, "Implement")
    second = run_pre_implement_check(paths, ctx, "Implement")
    assert first.allow_implement == second.allow_implement
    assert first.to_dict()["allow_implement"] == second.to_dict()["allow_implement"]
