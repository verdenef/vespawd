"""Projection engine — status.md and Notes enrichment (§7)."""

from __future__ import annotations

import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from vespawd_bridge import codes
from vespawd_bridge.cli.parse import VedawsSnapshot
from vespawd_bridge.manifest.paths import ResolvedPaths

MANAGED_NOTE_KEYS = (
    "**Vedaws phase:**",
    "**Orchestration state:**",
    "**Bridge sync:**",
    "**Blockers:**",
)


def _bridge_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_status_template() -> str:
    template_path = _bridge_root() / "sync" / "status.template.md"
    if template_path.is_file():
        return template_path.read_text(encoding="utf-8")
    return (
        "# POS status\n\n| Field | Value |\n|-------|--------|\n"
        "| Phase | {{phase}} |\n| App | {{app}} |\n| Handoff | {{handoff}} |\n"
        "| Docs (submission) | {{docs_submission}} |\n| Orchestration | {{orchestration}} |\n"
        "| Design gate | {{design_gate}} |\n| Last_sync | {{last_sync}} |\n| Blockers | {{blockers}} |\n\n"
        "_Orchestration projected by Vespawd Bridge. Do not edit manually._\n"
    )


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as handle:
        handle.write(content)
        temp_name = handle.name
    Path(temp_name).replace(path)


def read_app_status(current_task_path: Path) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if not current_task_path.is_file():
        warnings.append("current_task unreadable")
        return "unknown", warnings
    text = current_task_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"\*\*Status:\*\*\s*`?(\w+)`?", text)
    if match:
        return match.group(1), warnings
    return "unknown", warnings


def read_handoff_freshness(handoff_path: Path, *, max_age_hours: int = 48) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if not handoff_path.is_file():
        return "stale", warnings
    text = handoff_path.read_text(encoding="utf-8", errors="replace")
    footer = re.search(r"Last updated:\s*([0-9T:\-+.Z]+)", text, re.IGNORECASE)
    if not footer:
        warnings.append(codes.HANDOFF_STALE)
        return "stale", warnings
    try:
        stamp = datetime.fromisoformat(footer.group(1).replace("Z", "+00:00"))
        age = datetime.now(timezone.utc) - stamp.astimezone(timezone.utc)
        if age.total_seconds() > max_age_hours * 3600:
            warnings.append(codes.HANDOFF_STALE)
            return "stale", warnings
    except ValueError:
        warnings.append(codes.HANDOFF_STALE)
        return "stale", warnings
    return "fresh", warnings


def read_design_gate(design_gate_path: Path, *, skip_design: bool = False) -> str:
    if skip_design:
        return "skipped"
    if not design_gate_path.is_file():
        return "open"
    text = design_gate_path.read_text(encoding="utf-8", errors="replace").lower()
    if "ready for implementation" in text:
        return "ready"
    return "open"


def write_status(
    paths: ResolvedPaths,
    snapshot: VedawsSnapshot,
    *,
    blockers: list[str] | None = None,
    skip_design: bool = False,
    offline: bool = False,
    prior_phase: str | None = None,
) -> tuple[str, list[str]]:
    warnings: list[str] = []
    app_status, app_warnings = read_app_status(paths.current_task_path)
    warnings.extend(app_warnings)

    handoff, handoff_warnings = read_handoff_freshness(paths.handoff_path)
    warnings.extend(handoff_warnings)

    design_gate = read_design_gate(paths.design_gate_path, skip_design=skip_design)

    phase = snapshot.active_task_id or prior_phase or "unknown"
    if offline:
        phase = prior_phase or phase or "offline"

    orchestration = snapshot.project_state or ("offline" if offline else "unknown")
    docs_submission = "ready" if handoff == "fresh" else "pending"
    blocker_text = "; ".join(blockers) if blockers else "none"
    last_sync = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    template = load_status_template()
    content = (
        template.replace("{{phase}}", phase)
        .replace("{{app}}", app_status)
        .replace("{{handoff}}", handoff)
        .replace("{{docs_submission}}", docs_submission)
        .replace("{{orchestration}}", orchestration)
        .replace("{{design_gate}}", design_gate)
        .replace("{{last_sync}}", last_sync)
        .replace("{{blockers}}", blocker_text)
    )
    _atomic_write(paths.status_path, content)
    rel = _relative_to_workspace(paths.status_path, paths)
    return rel, warnings


def _relative_to_workspace(path: Path, paths: ResolvedPaths) -> str:
    for base in (paths.pos_root, paths.vedaws_project_root):
        try:
            return str(path.relative_to(base)).replace("\\", "/")
        except ValueError:
            continue
    return str(path)


def enrich_notes(
    paths: ResolvedPaths,
    *,
    vedaws_task_id: str,
    project_state: str,
    blockers: list[str] | None = None,
    existing_notes_phase: str | None = None,
) -> tuple[str | None, list[str]]:
    warnings: list[str] = []
    if not paths.current_task_path.is_file():
        return None, warnings

    text = paths.current_task_path.read_text(encoding="utf-8")
    managed = {
        "**Vedaws phase:**": vedaws_task_id,
        "**Orchestration state:**": project_state,
        "**Bridge sync:**": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "**Blockers:**": "; ".join(blockers) if blockers else "none",
    }

    if existing_notes_phase and existing_notes_phase != vedaws_task_id:
        warnings.append(codes.PROJECTION_DRIFT_CORRECTED)

    notes_match = re.search(r"(?ms)^## Notes\s*\n(.*?)(?=^## |\Z)", text)
    if notes_match:
        notes_body = notes_match.group(1)
        for key, value in managed.items():
            pattern = re.compile(rf"^- {re.escape(key)}.*$", re.MULTILINE)
            line = f"- {key} {value}"
            if pattern.search(notes_body):
                notes_body = pattern.sub(line, notes_body)
            else:
                notes_body = notes_body.rstrip() + f"\n{line}\n"
        new_text = text[: notes_match.start(1)] + notes_body + text[notes_match.end(1) :]
    else:
        block = "\n## Notes\n" + "\n".join(f"- {k} {v}" for k, v in managed.items()) + "\n"
        if "## Progress Log" in text:
            new_text = text.replace("## Progress Log", block + "## Progress Log", 1)
        else:
            new_text = text.rstrip() + block

    _atomic_write(paths.current_task_path, new_text)
    return _relative_to_workspace(paths.current_task_path, paths), warnings


def mirror_handoff(paths: ResolvedPaths, mirror_rel: str) -> str | None:
    if not paths.handoff_path.is_file():
        return None
    target = paths.vedaws_project_root / mirror_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(paths.handoff_path, target)
    return mirror_rel.replace("\\", "/")
