"""Unit tests — design-only phase gate (§8.2)."""

from __future__ import annotations

from pathlib import Path

from vespawd_bridge.validation.engine import validate_design_gate, validate_manifest_schema
from vespawd_bridge.manifest.model import ManifestModel, PhaseMapEntry


def test_design_only_phase_allows_without_design_ready(tmp_path: Path) -> None:
    design = tmp_path / "DESIGN.md"
    design.write_text("Status: not started\n", encoding="utf-8")
    result = validate_design_gate(
        "Define API contracts",
        design,
        ui_keywords=("ui",),
        vedaws_task_id="software.api-design",
    )
    assert result.passed


def test_design_only_phase_blocks_userspace_ui(tmp_path: Path) -> None:
    design = tmp_path / "DESIGN.md"
    design.write_text("Status: not started\n", encoding="utf-8")
    result = validate_design_gate(
        "Build dashboard UI screens",
        design,
        ui_keywords=("ui", "dashboard"),
        vedaws_task_id="software.architecture",
    )
    assert not result.passed


def test_validate_manifest_schema_rejects_bad_workflow() -> None:
    model = ManifestModel(
        vespawd_version="0.1.0",
        layout="sidecar",
        pos_root="../paws022",
        current_task="tasks/current_task.md",
        handoff="docs/HANDOFF.md",
        design_gate="design/DESIGN.md",
        status="tasks/status.md",
        vedaws_project_root=".",
        workflow_id="default",
        cli="vedaws",
        compat_vedaws=None,
        run_max_iterations=3,
        run_strict_mode=False,
        ui_keywords=(),
        phase_map=(PhaseMapEntry("scope", ("scope",)),),
        handoff_mirror=None,
        doctor_summary_max_chars=2000,
        manifest_path="/tmp/manifest.toml",
    )
    result = validate_manifest_schema(model)
    assert not result.passed
