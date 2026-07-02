"""Shared integration test fixtures."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

BRIDGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BRIDGE_ROOT.parents[1]
VEDAWS_ROOT = REPO_ROOT / "vedaws"


def vedaws_available() -> bool:
    try:
        runtime = VEDAWS_ROOT / "runtime"
        result = subprocess.run(
            [sys.executable, "-m", "vedaws", "version"],
            capture_output=True,
            env={"PYTHONPATH": str(runtime), **__import__("os").environ},
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


requires_vedaws = pytest.mark.skipif(not vedaws_available(), reason="vedaws CLI not available")


@pytest.fixture
def fixture_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "vespawd"
    main = ws / "main"
    paws = ws / "paws022"
    bridge = main / "bridge"
    bridge.mkdir(parents=True)
    shutil.copy(BRIDGE_ROOT / "manifest.toml", bridge / "manifest.toml")
    shutil.copytree(BRIDGE_ROOT / "sync", bridge / "sync")
    shutil.copytree(BRIDGE_ROOT / "spec", bridge / "spec")

    manifest = bridge / "manifest.toml"
    text = manifest.read_text(encoding="utf-8")
    text = text.replace('cli = "../../vedaws"', f'cli = "{VEDAWS_ROOT.as_posix()}"')
    manifest.write_text(text, encoding="utf-8")

    (paws / "tasks").mkdir(parents=True)
    (paws / "design").mkdir(parents=True)
    (paws / ".ai").mkdir(parents=True)
    (paws / "docs").mkdir(parents=True)
    (paws / "tasks" / "current_task.md").write_text(
        "**Status:** `idle`\n\n## Goal\n\nTest\n\n## Acceptance Criteria\n\n- [ ] x\n\n## Notes\n\n",
        encoding="utf-8",
    )
    (paws / "tasks" / "status.md").write_text("# POS status\n", encoding="utf-8")
    (paws / "tasks" / "backlog.md").write_text("# Backlog\n", encoding="utf-8")
    (paws / ".ai" / "project_context.md").write_text(
        "| Field | Value |\n|-------|--------|\n| Mode | sidecar |\n",
        encoding="utf-8",
    )
    (paws / "design" / "DESIGN.md").write_text(
        "## Status\n\n- **Design phase:** ready for implementation\n",
        encoding="utf-8",
    )
    (paws / "docs" / "HANDOFF_FOR_DOCUMENTER.md").write_text(
        "# Handoff\n\nLast updated: 2099-01-01T00:00:00Z\n",
        encoding="utf-8",
    )
    (main / "src").mkdir(parents=True)
    return ws


@pytest.fixture
def bridge_context(fixture_workspace: Path):
    from vespawd_bridge.api.types import BridgeContext

    return BridgeContext(workspace_root=str(fixture_workspace))
