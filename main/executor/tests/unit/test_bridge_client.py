"""Bridge client tests."""

from __future__ import annotations

import json
from pathlib import Path

from vespawd_executor.api.types import ExecutorContext
from vespawd_executor.bridge.client import BridgeClient


def test_bridge_client_missing_cli(tmp_path: Path) -> None:
    client = BridgeClient(tmp_path / "missing", tmp_path)
    result = client.invoke("sync_status", ExecutorContext(workspace_root=str(tmp_path)))
    assert not result.ok
    assert "Bridge CLI not found" in result.blockers[0]


def test_bridge_client_invoke_roundtrip(fixture_workspace: Path) -> None:
    paths_bridge = fixture_workspace / "main" / "bridge" / "bin" / "bridge"
    client = BridgeClient(paths_bridge, fixture_workspace)
    ctx = ExecutorContext(workspace_root=str(fixture_workspace), correlation_id="test-corr")
    result = client.invoke("sync_status", ctx, {})
    assert result.operation == "sync_status"
    assert result.correlation_id == "test-corr"
    assert isinstance(result.raw, dict)
