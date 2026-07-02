"""Validation engine (§8)."""

from __future__ import annotations

import re
from pathlib import Path

from vespawd_bridge import codes
from vespawd_bridge.cli.parse import VedawsSnapshot
from vespawd_bridge.manifest.model import ManifestModel
from vespawd_bridge.manifest.paths import ResolvedPaths
from vespawd_bridge.validation.result import ValidationResult

_IMPLEMENT_ALLOWED_STATES = frozenset({"planning", "ready", "executing", "recovering"})
_BLOCKED_STATES = frozenset({"blocked", "failed", "awaiting_approval", "completed", "archived", "created"})


def validate_layout(paths: ResolvedPaths) -> ValidationResult:
    result = ValidationResult()
    context_path = paths.project_context_path
    if not context_path.is_file():
        return result

    text = context_path.read_text(encoding="utf-8", errors="replace")
    mode_match = re.search(r"^\|\s*Mode\s*\|\s*(\w+)\s*\|", text, re.MULTILINE)
    if not mode_match:
        return result

    mode = mode_match.group(1).strip().lower()
    expected = paths.layout.lower()
    if expected == "sidecar" and mode not in {"sidecar", "integrated"}:
        pass
    if expected == "sidecar" and mode == "integrated":
        result.passed = False
        result.codes.append(codes.LAYOUT_CONFLICT)
        result.messages.append(f"project_context Mode={mode} conflicts with manifest layout={expected}")
    if expected == "integrated" and mode == "sidecar":
        result.passed = False
        result.codes.append(codes.LAYOUT_CONFLICT)
        result.messages.append(f"project_context Mode={mode} conflicts with manifest layout={expected}")

    if paths.layout == "sidecar":
        paws_src = paths.pos_root / "src"
        if paws_src.is_dir():
            result.passed = False
            result.codes.append(codes.LAYOUT_CONFLICT)
            result.messages.append("userspace must not live under paws022/src/ in sidecar layout")

    return result


def validate_version(manifest: ManifestModel, implementation_version: str) -> ValidationResult:
    result = ValidationResult()
    manifest_major = manifest.vespawd_version.split(".")[0]
    impl_major = implementation_version.split(".")[0]
    if manifest_major != impl_major:
        result.passed = False
        result.codes.append(codes.VERSION_MISMATCH)
        result.messages.append(
            f"manifest vespawd.version {manifest.vespawd_version} incompatible with bridge {implementation_version}"
        )
    elif manifest.vespawd_version != implementation_version:
        result.codes.append(codes.VERSION_MISMATCH)
        result.messages.append(
            f"minor version drift: manifest {manifest.vespawd_version}, bridge {implementation_version}"
        )

    if manifest.workflow_id != "software":
        result.passed = False
        result.codes.append(codes.INVALID_MANIFEST)
        result.messages.append("vedaws.workflow_id must be 'software' for v1")

    return result


def validate_manifest_integrity(paths: ResolvedPaths) -> ValidationResult:
    result = ValidationResult()
    if not paths.pos_root.is_dir():
        result.passed = False
        result.codes.append(codes.INVALID_PATH)
        result.messages.append(f"POS root missing: {paths.pos_root}")
    tasks_dir = paths.pos_root / "tasks"
    if not tasks_dir.is_dir():
        result.passed = False
        result.codes.append(codes.INVALID_PATH)
        result.messages.append(f"tasks/ missing under POS root: {tasks_dir}")
    return result


def validate_doctor(exit_code: int, summary: str, *, mode: str = "strict") -> ValidationResult:
    result = ValidationResult()
    if exit_code == 0:
        return result
    if mode == "soft":
        result.codes.append(codes.DOCTOR_WARN)
        result.messages.append(summary[:500] or "doctor reported warnings")
        return result
    result.passed = False
    result.codes.append(codes.DOCTOR_BLOCKED)
    result.messages.append(summary[:500] or "doctor failed")
    return result


def validate_manifest_schema(model: ManifestModel) -> ValidationResult:
    """Validate parsed manifest model (§5.1 step 6, §5.2)."""
    result = ValidationResult()
    if not model.vespawd_version:
        result.passed = False
        result.codes.append(codes.INVALID_MANIFEST)
        result.messages.append("[vespawd].version is required")
    if not model.workflow_id:
        result.passed = False
        result.codes.append(codes.INVALID_MANIFEST)
        result.messages.append("[vedaws].workflow_id is required")
    if model.workflow_id != "software":
        result.passed = False
        result.codes.append(codes.INVALID_MANIFEST)
        result.messages.append("vedaws.workflow_id must be 'software' for v1")
    return result


def validate_compat_vedaws(manifest: ManifestModel, vedaws_version: str | None) -> ValidationResult:
    """Optional Vedaws baseline check (§5.3, §8.5)."""
    result = ValidationResult()
    if not manifest.compat_vedaws or not vedaws_version:
        return result
    baseline_major = manifest.compat_vedaws.split(".")[0]
    runtime_major = vedaws_version.split(".")[0]
    if baseline_major != runtime_major:
        result.codes.append(codes.VERSION_MISMATCH)
        result.messages.append(
            f"Vedaws runtime {vedaws_version} may be incompatible with manifest baseline {manifest.compat_vedaws}"
        )
    return result


_DESIGN_ONLY_TASKS = frozenset({"scope", "architecture", "api-design"})


def validate_design_gate(
    current_task: str,
    design_gate_path: Path,
    *,
    skip_design: bool = False,
    design_later: bool = False,
    ui_keywords: tuple[str, ...],
    vedaws_task_id: str | None = None,
) -> ValidationResult:
    result = ValidationResult()
    if skip_design or design_later:
        result.codes.append(codes.DESIGN_GATE_OVERRIDDEN)
        result.messages.append("design gate overridden by session flags")
        return result

    haystack = current_task.lower()
    has_ui = any(keyword in haystack for keyword in ui_keywords)
    task_key = (vedaws_task_id or "").removeprefix("software.")
    if task_key in _DESIGN_ONLY_TASKS:
        if has_ui:
            result.passed = False
            result.codes.append(codes.DESIGN_GATE_BLOCKED)
            result.messages.append("design-only phase: userspace UI requires design path update")
        return result

    if not has_ui:
        return result

    if not design_gate_path.is_file():
        result.passed = False
        result.codes.append(codes.DESIGN_GATE_BLOCKED)
        result.messages.append("UI task requires DESIGN.md")
        return result

    design_text = design_gate_path.read_text(encoding="utf-8", errors="replace").lower()
    if "ready for implementation" not in design_text:
        result.passed = False
        result.codes.append(codes.DESIGN_GATE_BLOCKED)
        result.messages.append("DESIGN.md not ready for implementation")
    return result


def validate_workflow_eligibility(snapshot: VedawsSnapshot) -> ValidationResult:
    result = ValidationResult()
    state = snapshot.project_state.lower()
    if state in _BLOCKED_STATES:
        result.passed = False
        result.codes.append(codes.STATE_INELIGIBLE)
        result.messages.append(f"Vedaws state '{state}' forbids implement")
    elif state and state not in _IMPLEMENT_ALLOWED_STATES:
        result.passed = False
        result.codes.append(codes.STATE_INELIGIBLE)
        result.messages.append(f"Vedaws state '{state}' not eligible for implement")
    return result


def validate_task_alignment(current_task: str, snapshot: VedawsSnapshot, expected_task_id: str = "") -> ValidationResult:
    result = ValidationResult()
    if not expected_task_id or not snapshot.active_task_id:
        return result
    if snapshot.active_task_id != expected_task_id and expected_task_id not in current_task:
        result.codes.append(codes.WORKFLOW_TASK_MISMATCH)
        result.messages.append(
            f"PAWS task drift: expected {expected_task_id}, Vedaws active {snapshot.active_task_id}"
        )
    return result


def validate_artifacts(artifacts_stdout: str, exit_code: int) -> ValidationResult:
    result = ValidationResult()
    if exit_code == 0:
        return result
    result.passed = False
    result.codes.append(codes.ARTIFACTS_MISSING)
    missing_lines = [
        line.strip()
        for line in artifacts_stdout.splitlines()
        if "missing" in line.lower() or "[ ]" in line or "✗" in line
    ]
    if missing_lines:
        result.messages.extend(missing_lines[:10])
    else:
        result.messages.append("software artifacts check failed")
    return result


def validate_task_exists(snapshot: VedawsSnapshot, vedaws_task_id: str) -> ValidationResult:
    """Verify task is present in workflow before completion (§4.6)."""
    result = ValidationResult()
    if vedaws_task_id in snapshot.task_states:
        return result
    if not snapshot.task_states:
        return result
    result.passed = False
    result.codes.append(codes.TASK_COMPLETE_DENIED)
    result.messages.append(f"Task {vedaws_task_id} not found in active workflow")
    return result


def validate_workflow_corrupt(workflow_stdout: str) -> ValidationResult:
    result = ValidationResult()
    if "Invalid manifests" in workflow_stdout:
        result.passed = False
        result.codes.append(codes.WORKFLOW_CORRUPT)
        result.messages.append("workflow progress unreadable")
    return result
