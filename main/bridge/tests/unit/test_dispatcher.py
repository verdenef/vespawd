"""Unit tests — dispatcher prepare abort (§1.4, §11.1)."""

from __future__ import annotations

from pathlib import Path

from vespawd_bridge.api.invoke import invoke
from vespawd_bridge.api.types import BridgeContext


def test_dispatcher_aborts_without_manifest(tmp_path: Path) -> None:
    ctx = BridgeContext(workspace_root=str(tmp_path))
    result = invoke("bootstrap", ctx, {})
    assert not result.ok
    assert "missing_manifest" in result.codes
    assert result.vedaws_commands_run == []


def test_dispatcher_aborts_layout_conflict(tmp_path: Path) -> None:
    import shutil

    bridge_root = Path(__file__).resolve().parents[2]
    ws = tmp_path / "vespawd"
    main = ws / "main"
    paws = ws / "paws022"
    bridge = main / "bridge"
    bridge.mkdir(parents=True)
    shutil.copy(bridge_root / "manifest.toml", bridge / "manifest.toml")
    shutil.copytree(bridge_root / "spec", bridge / "spec")
    (paws / ".ai").mkdir(parents=True)
    (paws / ".ai" / "project_context.md").write_text(
        "| Field | Value |\n|-------|--------|\n| Mode | integrated |\n",
        encoding="utf-8",
    )
    (main / "src").mkdir(parents=True)

    ctx = BridgeContext(workspace_root=str(ws))
    result = invoke("bootstrap", ctx, {})
    assert not result.ok
    assert "layout_conflict" in result.codes
