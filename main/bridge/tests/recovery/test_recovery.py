"""Recovery tests (§11.3)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from vespawd_bridge.api.invoke import invoke
from vespawd_bridge.api.types import BridgeContext

BRIDGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BRIDGE_ROOT.parents[1]
VEDAWS_ROOT = REPO_ROOT / "vedaws"


def _vedaws_env():
    return {"PYTHONPATH": str(VEDAWS_ROOT / "runtime"), **__import__("os").environ}


def _vedaws_available() -> bool:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "vedaws", "version"],
            capture_output=True,
            env=_vedaws_env(),
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def _minimal_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "vespawd"
    main = ws / "main"
    paws = ws / "paws022"
    bridge = main / "bridge"
    bridge.mkdir(parents=True)
    shutil.copy(BRIDGE_ROOT / "manifest.toml", bridge / "manifest.toml")
    shutil.copytree(BRIDGE_ROOT / "spec", bridge / "spec")
    shutil.copytree(BRIDGE_ROOT / "sync", bridge / "sync")
    text = (bridge / "manifest.toml").read_text(encoding="utf-8").replace(
        'cli = "../../vedaws"', f'cli = "{VEDAWS_ROOT.as_posix()}"'
    )
    (bridge / "manifest.toml").write_text(text, encoding="utf-8")
    (paws / "tasks").mkdir(parents=True)
    (paws / ".ai").mkdir(parents=True)
    (paws / "tasks" / "status.md").write_text("# status\n", encoding="utf-8")
    (paws / ".ai" / "project_context.md").write_text("| Mode | sidecar |\n", encoding="utf-8")
    (main / "src").mkdir()
    return ws


@pytest.mark.skipif(not _vedaws_available(), reason="vedaws CLI not available")
def test_rebootstrap_after_partial_init(tmp_path: Path) -> None:
    ws = _minimal_workspace(tmp_path)
    main = ws / "main"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "vedaws",
            "init",
            "--template",
            "software",
            str(main),
            "--name",
            "partial",
        ],
        check=True,
        env=_vedaws_env(),
        capture_output=True,
    )
    ctx = BridgeContext(workspace_root=str(ws))
    first = invoke("bootstrap", ctx, {})
    second = invoke("bootstrap", ctx, {})
    assert first.ok, first.blockers
    assert second.ok, second.blockers


@pytest.mark.skipif(not _vedaws_available(), reason="vedaws CLI not available")
def test_workflow_corrupt_detected(tmp_path: Path) -> None:
    ws = _minimal_workspace(tmp_path)
    ctx = BridgeContext(workspace_root=str(ws))
    invoke("bootstrap", ctx, {})
    progress = ws / "main" / ".vedaws" / "workflow-progress.json"
    progress.write_text("{ not valid json", encoding="utf-8")
    gate = invoke(
        "pre_implement_check",
        ctx,
        {"current_task": "implement feature"},
    )
    assert "workflow_corrupt" in gate.codes or not gate.ok


def test_vedaws_missing_offline_sync(tmp_path: Path) -> None:
    ws = _minimal_workspace(tmp_path)
    text = (ws / "main" / "bridge" / "manifest.toml").read_text(encoding="utf-8").replace(
        f'cli = "{VEDAWS_ROOT.as_posix()}"', 'cli = "nonexistent-vedaws-binary"'
    )
    (ws / "main" / "bridge" / "manifest.toml").write_text(text, encoding="utf-8")
    ctx = BridgeContext(workspace_root=str(ws))
    result = invoke("sync_status", ctx, {})
    assert result.ok
    assert "orchestration_offline" in result.codes or "vedaws_missing" in result.codes
