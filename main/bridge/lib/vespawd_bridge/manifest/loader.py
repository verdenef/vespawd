"""Manifest loader (§1.5, §5)."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from vespawd_bridge import codes
from vespawd_bridge.manifest.model import ManifestModel, PhaseMapEntry
from vespawd_bridge.manifest.phase_map import DEFAULT_PHASE_MAP
from vespawd_bridge.validation.engine import validate_manifest_schema

REQUIRED_VESPAWD = ("version",)
REQUIRED_POS = ("root", "current_task", "handoff", "design_gate")
REQUIRED_VEDAWS = ("project_root", "workflow_id", "cli")


def find_manifest_path(workspace_root: Path) -> Path | None:
    candidates = [
        workspace_root / "main" / "bridge" / "manifest.toml",
        workspace_root / "bridge" / "manifest.toml",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _require_section(data: dict[str, Any], section: str) -> dict[str, Any]:
    value = data.get(section)
    if not isinstance(value, dict):
        raise ValueError(f"Missing required section [{section}]")
    return value


def _require_keys(section: dict[str, Any], keys: tuple[str, ...], section_name: str) -> None:
    missing = [key for key in keys if key not in section or section[key] in (None, "")]
    if missing:
        raise ValueError(f"Missing required keys in [{section_name}]: {', '.join(missing)}")


def _parse_phase_map(raw: dict[str, Any]) -> tuple[PhaseMapEntry, ...]:
    merged: dict[str, list[str]] = {
        entry.task_id: list(entry.keywords) for entry in DEFAULT_PHASE_MAP
    }
    for key, value in raw.items():
        if not key.startswith("phase_map."):
            continue
        task_id = key.removeprefix("phase_map.")
        if isinstance(value, dict) and "keywords" in value:
            merged[task_id] = [str(k).lower() for k in value["keywords"]]
        elif isinstance(value, str):
            merged[task_id] = [value.lower()]
        elif isinstance(value, list):
            merged[task_id] = [str(k).lower() for k in value]

    for task_id, section in raw.items():
        if task_id == "phase_map" or task_id.startswith("phase_map."):
            continue
    # Nested [phase_map.scope] style tables appear as phase_map.scope in flat tomllib? 
    # tomllib gives nested dict under phase_map key
    phase_map_section = raw.get("phase_map")
    if isinstance(phase_map_section, dict):
        for task_id, value in phase_map_section.items():
            if isinstance(value, dict) and "keywords" in value:
                merged[task_id] = [str(k).lower() for k in value["keywords"]]
            elif isinstance(value, list):
                merged[task_id] = [str(k).lower() for k in value]

    return tuple(
        PhaseMapEntry(task_id=task_id, keywords=tuple(keywords))
        for task_id, keywords in merged.items()
    )


def load_manifest(workspace_root: Path) -> tuple[ManifestModel | None, str | None]:
    manifest_path = find_manifest_path(workspace_root)
    if manifest_path is None:
        return None, codes.MISSING_MANIFEST

    try:
        raw = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return None, codes.INVALID_MANIFEST

    try:
        vespawd = _require_section(raw, "vespawd")
        pos = _require_section(raw, "pos")
        vedaws = _require_section(raw, "vedaws")
        _require_keys(vespawd, REQUIRED_VESPAWD, "vespawd")
        _require_keys(pos, REQUIRED_POS, "pos")
        _require_keys(vedaws, REQUIRED_VEDAWS, "vedaws")

        compat = raw.get("compat", {})
        run_section = raw.get("run", {})
        validation = raw.get("validation", {})
        projection = raw.get("projection", {})

        ui_keywords = validation.get("ui_keywords", [])
        if not isinstance(ui_keywords, list):
            ui_keywords = []

        layout = str(vespawd.get("layout", "sidecar"))
        model = ManifestModel(
            vespawd_version=str(vespawd["version"]),
            layout=layout,
            pos_root=str(pos["root"]),
            current_task=str(pos["current_task"]),
            handoff=str(pos["handoff"]),
            design_gate=str(pos["design_gate"]),
            status=str(pos.get("status", "tasks/status.md")),
            vedaws_project_root=str(vedaws["project_root"]),
            workflow_id=str(vedaws["workflow_id"]),
            cli=str(vedaws["cli"]),
            compat_vedaws=str(compat.get("vedaws")) if compat.get("vedaws") else None,
            run_max_iterations=int(run_section.get("max_iterations", 3)),
            run_strict_mode=bool(run_section.get("strict_mode", False)),
            ui_keywords=tuple(str(k).lower() for k in ui_keywords),
            phase_map=_parse_phase_map(raw),
            handoff_mirror=str(projection["handoff_mirror"])
            if projection.get("handoff_mirror")
            else None,
            doctor_summary_max_chars=int(projection.get("doctor_summary_max_chars", 2000)),
            manifest_path=str(manifest_path),
        )
        schema_val = validate_manifest_schema(model)
        if not schema_val.passed:
            return None, codes.INVALID_MANIFEST
        return model, None
    except (ValueError, TypeError):
        return None, codes.INVALID_MANIFEST
