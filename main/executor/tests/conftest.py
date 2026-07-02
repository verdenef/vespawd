"""Pytest fixtures."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
BRIDGE_ROOT = WORKSPACE_ROOT / "main" / "bridge"
VEDAWS_ROOT = WORKSPACE_ROOT / "vedaws"


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
def workspace_root() -> Path:
    return WORKSPACE_ROOT


@pytest.fixture
def fixture_workspace(tmp_path: Path) -> Path:
    """Minimal sidecar workspace with Bridge CLI wired to repo vedaws."""
    root = tmp_path / "vespawd"
    paws = root / "paws022"
    main = root / "main"
    bridge = main / "bridge"

    paws.mkdir(parents=True)
    (paws / ".ai").mkdir()
    (paws / "tasks").mkdir()
    (paws / "design").mkdir()
    (paws / "docs").mkdir()
    (paws / ".ai" / "project_context.md").write_text(
        """# Project Context

## Product
- **Name:** testapp

## Layout
| Field | Value |
|-------|--------|
| Mode | sidecar |
| Application code | `../main/src/` |
""",
        encoding="utf-8",
    )
    (paws / "tasks" / "current_task.md").write_text(
        "**Status:** `idle`\n\n### Goal\n\nIdle\n",
        encoding="utf-8",
    )
    (paws / "tasks" / "status.md").write_text("# Status\n", encoding="utf-8")
    (paws / "design" / "DESIGN.md").write_text(
        "## Status\n\n- **Design phase:** ready for implementation\n",
        encoding="utf-8",
    )
    (paws / "docs" / "HANDOFF_FOR_DOCUMENTER.md").write_text(
        "# Handoff\n\nLast updated: 2099-01-01T00:00:00Z\n",
        encoding="utf-8",
    )

    main.mkdir()
    (main / "src").mkdir()
    bridge.mkdir(parents=True)

    shutil.copy(BRIDGE_ROOT / "manifest.toml", bridge / "manifest.toml")
    shutil.copytree(BRIDGE_ROOT / "sync", bridge / "sync")
    shutil.copytree(BRIDGE_ROOT / "spec", bridge / "spec")
    manifest = bridge / "manifest.toml"
    text = manifest.read_text(encoding="utf-8")
    text = text.replace('cli = "../vedaws"', f'cli = "{VEDAWS_ROOT.as_posix()}"')
    text = text.replace('cli = "../../vedaws"', f'cli = "{VEDAWS_ROOT.as_posix()}"')
    manifest.write_text(text, encoding="utf-8")

    (bridge / "bin").mkdir()
    shutil.copy(BRIDGE_ROOT / "bin" / "bridge", bridge / "bin" / "bridge")
    shutil.copytree(BRIDGE_ROOT / "lib", bridge / "lib")

    return root
