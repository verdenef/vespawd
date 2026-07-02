"""post_implement orchestration unit tests (§7 guard + §8.3 hooks)."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from vespawd_executor.api.types import ExecutorContext
from vespawd_executor.bridge.client import BridgeResultView
from vespawd_executor.orchestration.implement import orchestrate_post_implement
from vespawd_executor.paths.resolver import resolve_workspace_paths


def _paths(fixture_workspace):
    return resolve_workspace_paths(fixture_workspace)


def _ok_view(op: str) -> BridgeResultView:
    return BridgeResultView(ok=True, operation=op, codes=["ok"])


@patch("vespawd_executor.orchestration.implement.BridgeClient")
def test_success_records_and_hooks(mock_cls, fixture_workspace) -> None:
    mock = MagicMock()
    mock_cls.return_value = mock
    mock.invoke.side_effect = [
        _ok_view("post_implement"),
        _ok_view("sync_status"),
    ]
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = orchestrate_post_implement(
        _paths(fixture_workspace),
        ctx,
        ["main/src/service.py"],
        vedaws_task_id="software.implement",
        logged_at=date(2026, 7, 2),
    )
    assert result.ok
    assert result.progress_logged
    assert result.steps_completed == ["progress_log", "bridge.post_implement", "bridge.sync_status"]
    ops = [c.args[0] for c in mock.invoke.call_args_list]
    assert ops == ["post_implement", "sync_status"]
    payload = mock.invoke.call_args_list[0].args[2]
    assert payload["vedaws_task_id"] == "software.implement"
    assert payload["changed_paths"] == ["main/src/service.py"]


@patch("vespawd_executor.orchestration.implement.BridgeClient")
def test_forbidden_edit_blocks_before_hooks(mock_cls, fixture_workspace) -> None:
    mock = MagicMock()
    mock_cls.return_value = mock
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = orchestrate_post_implement(
        _paths(fixture_workspace),
        ctx,
        ["main/src/ok.py", "paws022/.ai/executor_rules.md"],
        logged_at=date(2026, 7, 2),
    )
    assert not result.ok
    assert result.blockers
    assert not result.steps_completed
    mock.invoke.assert_not_called()


@patch("vespawd_executor.orchestration.implement.BridgeClient")
def test_unknown_path_warns_but_proceeds(mock_cls, fixture_workspace) -> None:
    mock = MagicMock()
    mock_cls.return_value = mock
    mock.invoke.side_effect = [_ok_view("post_implement"), _ok_view("sync_status")]
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = orchestrate_post_implement(
        _paths(fixture_workspace),
        ctx,
        ["main/src/a.py", "README.md"],
        logged_at=date(2026, 7, 2),
    )
    assert result.ok
    assert any("unclassified" in w for w in result.warnings)


@patch("vespawd_executor.orchestration.implement.BridgeClient")
def test_nonstrict_worker_failure_is_warning(mock_cls, fixture_workspace) -> None:
    mock = MagicMock()
    mock_cls.return_value = mock
    # Bridge post_implement non-strict: ok=True with cli_failed as warning.
    mock.invoke.side_effect = [
        BridgeResultView(
            ok=True,
            operation="post_implement",
            codes=["cli_failed", "ok"],
            warnings=["vedaws run reported worker failures"],
        ),
        _ok_view("sync_status"),
    ]
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = orchestrate_post_implement(
        _paths(fixture_workspace), ctx, ["main/src/a.py"], logged_at=date(2026, 7, 2)
    )
    assert result.ok
    assert not result.blockers
    assert any("worker failures" in w for w in result.warnings)


@patch("vespawd_executor.orchestration.implement.BridgeClient")
def test_strict_failure_blocks(mock_cls, fixture_workspace) -> None:
    mock = MagicMock()
    mock_cls.return_value = mock
    mock.invoke.side_effect = [
        BridgeResultView(
            ok=False,
            operation="post_implement",
            codes=["cli_failed"],
            blockers=["post_implement strict_mode: run failed"],
        ),
        _ok_view("sync_status"),
    ]
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = orchestrate_post_implement(
        _paths(fixture_workspace), ctx, ["main/src/a.py"], logged_at=date(2026, 7, 2)
    )
    assert not result.ok
    assert result.blockers


@patch("vespawd_executor.orchestration.implement.BridgeClient")
def test_bridge_missing_blocks(mock_cls, fixture_workspace) -> None:
    mock = MagicMock()
    mock_cls.return_value = mock
    mock.invoke.side_effect = [
        BridgeResultView(
            ok=False,
            operation="post_implement",
            codes=["bridge_invoke_failed"],
            blockers=["Bridge invoke produced no result"],
        ),
        _ok_view("sync_status"),
    ]
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = orchestrate_post_implement(
        _paths(fixture_workspace), ctx, ["main/src/a.py"], logged_at=date(2026, 7, 2)
    )
    assert not result.ok
    assert result.blockers


@patch("vespawd_executor.orchestration.implement.BridgeClient")
def test_offline_sync_does_not_block(mock_cls, fixture_workspace) -> None:
    mock = MagicMock()
    mock_cls.return_value = mock
    mock.invoke.side_effect = [
        _ok_view("post_implement"),
        BridgeResultView(
            ok=True,
            operation="sync_status",
            codes=["orchestration_offline"],
            warnings=["vedaws offline"],
        ),
    ]
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = orchestrate_post_implement(
        _paths(fixture_workspace), ctx, ["main/src/a.py"], logged_at=date(2026, 7, 2)
    )
    assert result.ok
    assert not result.blockers


@patch("vespawd_executor.orchestration.implement.BridgeClient")
def test_idempotent_repeated(mock_cls, fixture_workspace) -> None:
    mock = MagicMock()
    mock_cls.return_value = mock
    mock.invoke.side_effect = [
        _ok_view("post_implement"),
        _ok_view("sync_status"),
        _ok_view("post_implement"),
        _ok_view("sync_status"),
    ]
    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    paths = _paths(fixture_workspace)
    first = orchestrate_post_implement(
        paths, ctx, ["main/src/a.py"], logged_at=date(2026, 7, 2)
    )
    task_after_first = paths.current_task_path.read_text(encoding="utf-8")
    second = orchestrate_post_implement(
        paths, ctx, ["main/src/a.py"], logged_at=date(2026, 7, 2)
    )
    task_after_second = paths.current_task_path.read_text(encoding="utf-8")
    assert first.ok and second.ok
    assert first.progress_logged is True
    assert second.progress_logged is False
    assert task_after_first == task_after_second
