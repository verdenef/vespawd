"""Unit tests — validation engine (§11.1)."""

from __future__ import annotations

from pathlib import Path

from vespawd_bridge.validation.engine import validate_design_gate


def test_design_gate_blocks_ui_without_design(tmp_path: Path) -> None:
    design = tmp_path / "DESIGN.md"
    design.write_text("Status: in progress\n", encoding="utf-8")
    result = validate_design_gate(
        "Build the dashboard UI",
        design,
        ui_keywords=("ui", "dashboard"),
    )
    assert not result.passed


def test_design_gate_skip_override(tmp_path: Path) -> None:
    result = validate_design_gate(
        "Build UI",
        tmp_path / "missing.md",
        skip_design=True,
        ui_keywords=("ui",),
    )
    assert result.passed
