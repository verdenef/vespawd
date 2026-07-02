"""Integration tests — bootstrap and sync (§11.2)."""

from __future__ import annotations

from pathlib import Path

from vespawd_bridge.api.invoke import invoke

from tests.integration.conftest import requires_vedaws


@requires_vedaws
def test_bootstrap_creates_vedaws(fixture_workspace: Path, bridge_context) -> None:
    result = invoke("bootstrap", bridge_context, {})
    assert result.ok, result.blockers
    assert (fixture_workspace / "main" / ".vedaws" / "project.toml").is_file()
    assert any("doctor" in cmd for cmd in result.vedaws_commands_run)


@requires_vedaws
def test_sync_status_writes_status(fixture_workspace: Path, bridge_context) -> None:
    invoke("bootstrap", bridge_context, {})
    result = invoke("sync_status", bridge_context, {})
    assert result.ok
    assert result.files_touched
    status = (fixture_workspace / "paws022" / "tasks" / "status.md").read_text(encoding="utf-8")
    assert "Last_sync" in status
