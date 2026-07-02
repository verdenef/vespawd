"""Startup sequence tests (§3.6–3.7)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from vespawd_executor.bridge.client import BridgeResultView
from vespawd_executor.startup.sequence import run_startup


def _ok_sync() -> BridgeResultView:
    return BridgeResultView(
        ok=True,
        operation="sync_status",
        codes=["ok"],
        project_state="initialized",
    )


def _ok_bootstrap() -> BridgeResultView:
    return BridgeResultView(
        ok=True,
        operation="bootstrap",
        codes=["ok"],
        project_state="initialized",
        doctor_summary="doctor ok",
    )


def test_startup_validation_failure_missing_pos(tmp_path: Path) -> None:
    root = tmp_path / "bad"
    (root / "main" / "bridge").mkdir(parents=True)
    (root / "main" / "bridge" / "manifest.toml").write_text(
        '[vespawd]\nlayout="sidecar"\n[pos]\nroot="../paws022"\n[vedaws]\nproject_root="."\n',
        encoding="utf-8",
    )
    result = run_startup(root)
    assert not result.ok
    assert any("POS root" in b for b in result.blockers)


@patch("vespawd_executor.startup.sequence.BridgeClient.invoke")
def test_startup_bootstraps_when_vedaws_missing(
    mock_invoke, fixture_workspace: Path
) -> None:
    mock_invoke.side_effect = [_ok_bootstrap(), _ok_sync()]
    result = run_startup(fixture_workspace)
    assert result.bootstrap_invoked
    assert result.sync_invoked
    assert result.ok
    assert mock_invoke.call_count == 2
    assert mock_invoke.call_args_list[0].args[0] == "bootstrap"


@patch("vespawd_executor.startup.sequence.BridgeClient.invoke")
def test_startup_sync_only_when_vedaws_exists(
    mock_invoke, fixture_workspace: Path
) -> None:
    vedaws = fixture_workspace / "main" / ".vedaws"
    vedaws.mkdir(parents=True)
    (vedaws / "project.toml").write_text('name="x"\n', encoding="utf-8")

    mock_invoke.return_value = _ok_sync()
    result = run_startup(fixture_workspace)
    assert not result.bootstrap_invoked
    assert result.sync_invoked
    assert result.ok
    mock_invoke.assert_called_once()
    assert mock_invoke.call_args.args[0] == "sync_status"


@patch("vespawd_executor.startup.sequence.BridgeClient.invoke")
def test_startup_blocks_on_doctor(mock_invoke, fixture_workspace: Path) -> None:
    vedaws = fixture_workspace / "main" / ".vedaws"
    vedaws.mkdir(parents=True)
    (vedaws / "project.toml").write_text('name="x"\n', encoding="utf-8")

    mock_invoke.return_value = BridgeResultView(
        ok=False,
        operation="sync_status",
        codes=["doctor_blocked"],
        blockers=["doctor failed"],
        doctor_summary="blocking issue",
    )
    result = run_startup(fixture_workspace)
    assert not result.ok
    assert any("doctor" in b.lower() for b in result.blockers)
