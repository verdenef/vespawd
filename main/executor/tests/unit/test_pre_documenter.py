"""pre_documenter orchestration unit tests (§8.5)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from vespawd_executor.api.types import ExecutorContext
from vespawd_executor.bridge.client import BridgeResultView
from vespawd_executor.orchestration.documenter import orchestrate_pre_documenter
from vespawd_executor.paths.resolver import resolve_workspace_paths


def _paths(fixture_workspace):
    return resolve_workspace_paths(fixture_workspace)


@patch("vespawd_executor.orchestration.documenter.BridgeClient")
def test_documenter_ready(mock_cls, fixture_workspace) -> None:
    mock = MagicMock()
    mock_cls.return_value = mock
    mock.invoke.return_value = BridgeResultView(
        ok=True, operation="pre_documenter", codes=["ok"], project_state="documenting"
    )
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = orchestrate_pre_documenter(_paths(fixture_workspace), ctx)
    assert result.ok
    assert result.handoff_ready
    assert mock.invoke.call_args.args[0] == "pre_documenter"


@patch("vespawd_executor.orchestration.documenter.BridgeClient")
def test_documenter_artifacts_missing_blocks(mock_cls, fixture_workspace) -> None:
    mock = MagicMock()
    mock_cls.return_value = mock
    mock.invoke.return_value = BridgeResultView(
        ok=False,
        operation="pre_documenter",
        codes=["artifacts_missing"],
        blockers=["missing api_contracts.md"],
    )
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = orchestrate_pre_documenter(_paths(fixture_workspace), ctx)
    assert not result.ok
    assert result.artifacts_missing
    assert not result.handoff_ready


@patch("vespawd_executor.orchestration.documenter.BridgeClient")
def test_documenter_stale_handoff_warns(mock_cls, fixture_workspace) -> None:
    mock = MagicMock()
    mock_cls.return_value = mock
    mock.invoke.return_value = BridgeResultView(
        ok=True,
        operation="pre_documenter",
        codes=["ok", "handoff_stale"],
        warnings=["HANDOFF stale"],
    )
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = orchestrate_pre_documenter(_paths(fixture_workspace), ctx)
    assert result.ok
    assert result.handoff_stale
    assert not result.handoff_ready


@patch("vespawd_executor.orchestration.documenter.BridgeClient")
def test_documenter_doctor_blocked(mock_cls, fixture_workspace) -> None:
    mock = MagicMock()
    mock_cls.return_value = mock
    mock.invoke.return_value = BridgeResultView(
        ok=False,
        operation="pre_documenter",
        codes=["doctor_blocked"],
        blockers=["doctor failed"],
        doctor_summary="1 failure",
    )
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = orchestrate_pre_documenter(_paths(fixture_workspace), ctx)
    assert not result.ok
    assert result.doctor_blocked


@patch("vespawd_executor.orchestration.documenter.BridgeClient")
def test_documenter_bridge_failure_blocks(mock_cls, fixture_workspace) -> None:
    mock = MagicMock()
    mock_cls.return_value = mock
    mock.invoke.return_value = BridgeResultView(
        ok=False,
        operation="pre_documenter",
        codes=["bridge_invoke_failed"],
        blockers=["no result"],
    )
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = orchestrate_pre_documenter(_paths(fixture_workspace), ctx)
    assert not result.ok


@patch("vespawd_executor.orchestration.documenter.BridgeClient")
def test_documenter_idempotent(mock_cls, fixture_workspace) -> None:
    mock = MagicMock()
    mock_cls.return_value = mock
    mock.invoke.return_value = BridgeResultView(ok=True, operation="pre_documenter", codes=["ok"])
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    paths = _paths(fixture_workspace)
    first = orchestrate_pre_documenter(paths, ctx)
    second = orchestrate_pre_documenter(paths, ctx)
    assert first.to_dict()["handoff_ready"] == second.to_dict()["handoff_ready"]
