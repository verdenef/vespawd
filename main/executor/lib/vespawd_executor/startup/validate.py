"""Startup validation (Executor Spec §3.4)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from vespawd_executor.api.types import SessionOptions
from vespawd_executor.paths.resolver import WorkspacePaths


@dataclass
class ValidationResult:
    passed: bool = True
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


_STATUS_RE = re.compile(r"^\s*Status:\s*(\S+)", re.MULTILINE | re.IGNORECASE)
_GOAL_RE = re.compile(r"^###\s+Goal\s*$", re.MULTILINE | re.IGNORECASE)


def validate_layout_discoverable(paths: WorkspacePaths) -> ValidationResult:
    result = ValidationResult()
    if not paths.manifest.manifest_path.is_file():
        result.passed = False
        result.blockers.append("Bridge manifest missing at main/bridge/manifest.toml")
    if not paths.pos_root.is_dir():
        result.passed = False
        result.blockers.append(f"POS root not found: {paths.pos_root}")
    return result


def validate_userspace_resolvable(paths: WorkspacePaths) -> ValidationResult:
    result = ValidationResult()
    if not paths.vedaws_project_root.is_dir():
        result.passed = False
        result.blockers.append(f"Vedaws project root missing: {paths.vedaws_project_root}")
        return result
    parent = paths.userspace_root.parent
    if not parent.is_dir():
        result.passed = False
        result.blockers.append(f"Userspace parent missing: {parent}")
    return result


def validate_layout_consistency(paths: WorkspacePaths) -> ValidationResult:
    result = ValidationResult()
    ctx_mode = (paths.layout_from_context or "").lower()
    manifest_layout = paths.layout_from_manifest.lower()
    if ctx_mode and ctx_mode != manifest_layout:
        result.warnings.append(
            f"Layout mismatch: project_context Mode={ctx_mode}, "
            f"manifest layout={manifest_layout} (Bridge may emit layout_conflict)"
        )
    return result


def validate_concurrent_task(
    paths: WorkspacePaths,
    session: SessionOptions,
    incoming_goal: str | None = None,
) -> ValidationResult:
    """§3.4: block supersede without explicit confirmation."""
    result = ValidationResult()
    task_path = paths.current_task_path
    if not task_path.is_file() or not incoming_goal:
        return result

    text = task_path.read_text(encoding="utf-8", errors="replace")
    status_match = _STATUS_RE.search(text)
    if not status_match:
        return result

    status = status_match.group(1).lower()
    if status != "in_progress":
        return result

    if incoming_goal.lower() in text.lower():
        return result

    if session.supersede_active_task:
        result.warnings.append("Superseding in_progress task per session confirmation")
        return result

    result.passed = False
    result.blockers.append(
        "current_task.md is in_progress with a different goal; "
        "confirm supersede before continuing"
    )
    return result


def validate_startup(
    paths: WorkspacePaths,
    session: SessionOptions,
    *,
    incoming_goal: str | None = None,
    require_master_prompt: bool = False,
    has_master_prompt: bool = False,
) -> ValidationResult:
    """Aggregate §3.4 checks before parse/write/sync."""
    combined = ValidationResult()
    for partial in (
        validate_layout_discoverable(paths),
        validate_userspace_resolvable(paths),
        validate_layout_consistency(paths),
        validate_concurrent_task(paths, session, incoming_goal),
    ):
        combined.blockers.extend(partial.blockers)
        combined.warnings.extend(partial.warnings)
        if not partial.passed:
            combined.passed = False

    if require_master_prompt and not has_master_prompt:
        combined.passed = False
        combined.blockers.append("Master Prompt required for this operation")

    return combined
