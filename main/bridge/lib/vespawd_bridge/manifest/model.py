"""Immutable manifest model (§5)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhaseMapEntry:
    task_id: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class ManifestModel:
    vespawd_version: str
    layout: str
    pos_root: str
    current_task: str
    handoff: str
    design_gate: str
    status: str
    vedaws_project_root: str
    workflow_id: str
    cli: str
    compat_vedaws: str | None
    run_max_iterations: int
    run_strict_mode: bool
    ui_keywords: tuple[str, ...]
    phase_map: tuple[PhaseMapEntry, ...]
    handoff_mirror: str | None
    doctor_summary_max_chars: int
    manifest_path: str
