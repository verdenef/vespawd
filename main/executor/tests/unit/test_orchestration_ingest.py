"""Ingest orchestration unit tests (§5.3)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

from vespawd_executor.api.types import ExecutorContext
from vespawd_executor.bridge.client import BridgeResultView
from vespawd_executor.orchestration.ingest import orchestrate_master_prompt_from_text
from vespawd_executor.paths.resolver import resolve_workspace_paths

FIXTURES = __import__("pathlib").Path(__file__).resolve().parents[1] / "fixtures"
SAMPLE = (FIXTURES / "sample_master_prompt.md").read_text(encoding="utf-8")
FIXED_TS = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _ok_ingest() -> BridgeResultView:
    return BridgeResultView(
        ok=True,
        operation="ingest_master_prompt",
        codes=["ok"],
        vedaws_task_id="software.scope",
        project_state="planning",
    )


def _ok_sync() -> BridgeResultView:
    return BridgeResultView(
        ok=True,
        operation="sync_status",
        codes=["ok"],
        project_state="planning",
        files_touched=["tasks/status.md"],
    )


@patch("vespawd_executor.orchestration.ingest.BridgeClient")
def test_ingest_sequence_order(mock_client_cls, fixture_workspace) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.invoke.side_effect = [_ok_ingest(), _ok_sync()]

    ctx = ExecutorContext(workspace_root=str(fixture_workspace))
    result = orchestrate_master_prompt_from_text(
        SAMPLE,
        fixture_workspace,
        ctx,
        started_at=date(2026, 6, 1),
        synced_at=FIXED_TS,
    )

    assert result.ok, result.blockers
    assert result.steps_completed == [
        "paws_scheduler",
        "bridge.ingest_master_prompt",
        "bridge.sync_status",
        "handoff_seed",
    ]
    assert mock_client.invoke.call_count == 2
    assert mock_client.invoke.call_args_list[0].args[0] == "ingest_master_prompt"
    assert mock_client.invoke.call_args_list[1].args[0] == "sync_status"
    assert result.vedaws_task_id == "software.scope"


@patch("vespawd_executor.orchestration.ingest.BridgeClient")
def test_ingest_failure_still_syncs(mock_client_cls, fixture_workspace) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.invoke.side_effect = [
        BridgeResultView(
            ok=False,
            operation="ingest_master_prompt",
            codes=["state_transition_denied"],
            blockers=["denied"],
            recovery=[
                {
                    "code": "state_transition_denied",
                    "action": "retry",
                    "retry_operation": "ingest_master_prompt",
                }
            ],
        ),
        _ok_sync(),
    ]

    result = orchestrate_master_prompt_from_text(
        SAMPLE, fixture_workspace, synced_at=FIXED_TS
    )
    assert not result.ok
    assert result.block_implement
    assert result.sync_status is not None
    assert len(result.recovery) >= 1
    assert mock_client.invoke.call_count == 2


@patch("vespawd_executor.orchestration.ingest.BridgeClient")
def test_offline_sync_after_ingest(mock_client_cls, fixture_workspace) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.invoke.side_effect = [
        _ok_ingest(),
        BridgeResultView(
            ok=True,
            operation="sync_status",
            codes=["orchestration_offline", "vedaws_missing"],
            warnings=["offline"],
        ),
    ]

    result = orchestrate_master_prompt_from_text(
        SAMPLE, fixture_workspace, synced_at=FIXED_TS
    )
    assert result.ok
    assert not result.block_implement
    assert any("offline" in w.lower() for w in result.warnings)


@patch("vespawd_executor.orchestration.ingest.BridgeClient")
def test_idempotent_orchestration(mock_client_cls, fixture_workspace) -> None:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.invoke.side_effect = [_ok_ingest(), _ok_sync()] * 2

    first = orchestrate_master_prompt_from_text(
        SAMPLE, fixture_workspace, synced_at=FIXED_TS, started_at=date(2026, 6, 1)
    )
    paths = resolve_workspace_paths(fixture_workspace)
    context_snap = paths.project_context_path.read_text(encoding="utf-8")
    task_snap = paths.current_task_path.read_text(encoding="utf-8")
    backlog_snap = (paths.pos_root / "tasks" / "backlog.md").read_text(encoding="utf-8")
    second = orchestrate_master_prompt_from_text(
        SAMPLE, fixture_workspace, synced_at=FIXED_TS, started_at=date(2026, 6, 1)
    )
    assert first.ok and second.ok
    assert second.paws_sync and second.paws_sync.backlog_appended == 0
    assert paths.project_context_path.read_text(encoding="utf-8") == context_snap
    assert paths.current_task_path.read_text(encoding="utf-8") == task_snap
    assert (paths.pos_root / "tasks" / "backlog.md").read_text(encoding="utf-8") == backlog_snap
