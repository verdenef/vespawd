"""Parse Vedaws CLI text output into VedawsSnapshot (§3.3)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class VedawsSnapshot:
    project_state: str = ""
    active_workflow_id: str = ""
    active_task_id: str = ""
    task_states: dict[str, str] = field(default_factory=dict)
    doctor_ok: bool = True
    doctor_summary: str = ""
    artifacts_report: str = ""
    raw_outputs: dict[str, str] = field(default_factory=dict)


_VEDAWS_VERSION = re.compile(r"vedaws\s+(\S+)")
_TASK_LINE = re.compile(r"^\s+(\S+\.\S+)\s+\[(\w+)\]", re.MULTILINE)
_PROJECT_STATE = re.compile(r"^Project state:\s+(.+)$", re.MULTILINE)
_STATE_LINE = re.compile(r"^State:\s+(.+)$", re.MULTILINE)
_WORKFLOW_STATUS = re.compile(r"^Status:\s+(\w+)$", re.MULTILINE)


def parse_vedaws_version(stdout: str) -> str | None:
    match = _VEDAWS_VERSION.search(stdout)
    return match.group(1) if match else None


def parse_status_output(stdout: str) -> VedawsSnapshot:
    snapshot = VedawsSnapshot()
    match = _PROJECT_STATE.search(stdout)
    if match:
        snapshot.project_state = match.group(1).strip()
    return snapshot


def parse_workflow_show(stdout: str, workflow_id: str) -> VedawsSnapshot:
    snapshot = VedawsSnapshot(active_workflow_id=workflow_id)

    for task_key, status in _TASK_LINE.findall(stdout):
        snapshot.task_states[task_key] = status
        if status in {"ready", "in_progress", "running"}:
            snapshot.active_task_id = task_key

    if not snapshot.active_task_id:
        for task_key, status in snapshot.task_states.items():
            if status == "ready":
                snapshot.active_task_id = task_key
                break
    return snapshot


def merge_snapshots(*snapshots: VedawsSnapshot) -> VedawsSnapshot:
    merged = VedawsSnapshot()
    for snapshot in snapshots:
        if snapshot.project_state:
            merged.project_state = snapshot.project_state
        if snapshot.active_workflow_id:
            merged.active_workflow_id = snapshot.active_workflow_id
        if snapshot.active_task_id:
            merged.active_task_id = snapshot.active_task_id
        merged.task_states.update(snapshot.task_states)
        merged.doctor_ok = merged.doctor_ok and snapshot.doctor_ok
        if snapshot.doctor_summary:
            merged.doctor_summary = snapshot.doctor_summary
        if snapshot.artifacts_report:
            merged.artifacts_report = snapshot.artifacts_report
        merged.raw_outputs.update(snapshot.raw_outputs)
    return merged


def parse_doctor(stdout: str, stderr: str, exit_code: int) -> VedawsSnapshot:
    text = f"{stdout}\n{stderr}".strip()
    return VedawsSnapshot(
        doctor_ok=exit_code == 0,
        doctor_summary=text,
        raw_outputs={"doctor": text},
    )


def parse_artifacts(stdout: str, stderr: str, exit_code: int) -> VedawsSnapshot:
    text = f"{stdout}\n{stderr}".strip()
    return VedawsSnapshot(
        doctor_ok=exit_code == 0,
        artifacts_report=text,
        raw_outputs={"software_artifacts": text},
    )


def parse_state(stdout: str) -> VedawsSnapshot:
    match = _STATE_LINE.search(stdout) or _PROJECT_STATE.search(stdout)
    state = match.group(1).strip() if match else ""
    return VedawsSnapshot(project_state=state, raw_outputs={"state": stdout})
