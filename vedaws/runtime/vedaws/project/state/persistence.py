"""Persist project state and transition history."""

from __future__ import annotations

import json
import tomllib
from datetime import datetime, timezone
from pathlib import Path

from vedaws.project.state.models import StateValidationError, TransitionRecord
from vedaws.project.state.states import ProjectState

STATE_FILE_NAME = "state.toml"
HISTORY_FILE_NAME = "transitions.jsonl"


def state_file_path(project_dir: Path) -> Path:
    return project_dir / STATE_FILE_NAME


def history_file_path(project_dir: Path) -> Path:
    return project_dir / HISTORY_FILE_NAME


def load_current_state(project_dir: Path, *, fallback: ProjectState | None = None) -> ProjectState:
    path = state_file_path(project_dir)
    if not path.is_file():
        if fallback is not None:
            return fallback
        raise StateValidationError(f"State file not found: {path}")

    with path.open("rb") as handle:
        data = tomllib.load(handle)

    state_data = data.get("state", data)
    raw = str(state_data.get("current", "")).strip()
    state = ProjectState.parse(raw)
    if state is None:
        raise StateValidationError(f"Invalid project state in {path}: {raw!r}")
    return state


def save_current_state(project_dir: Path, state: ProjectState) -> None:
    project_dir.mkdir(parents=True, exist_ok=True)
    path = state_file_path(project_dir)
    updated_at = datetime.now(timezone.utc).isoformat()
    content = (
        f'# Vedaws project state\n\n'
        f'[state]\n'
        f'current = "{state.value}"\n'
        f'updated_at = "{updated_at}"\n'
    )
    path.write_text(content, encoding="utf-8")


def load_history(project_dir: Path) -> list[TransitionRecord]:
    path = history_file_path(project_dir)
    if not path.is_file():
        return []

    records: list[TransitionRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(TransitionRecord.from_dict(json.loads(line)))
    return records


def append_history(project_dir: Path, record: TransitionRecord) -> None:
    project_dir.mkdir(parents=True, exist_ok=True)
    path = history_file_path(project_dir)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.to_dict()) + "\n")


def initialize_state(project_dir: Path, initial: ProjectState = ProjectState.CREATED) -> None:
    save_current_state(project_dir, initial)
    history_path = history_file_path(project_dir)
    if not history_path.exists():
        history_path.write_text("", encoding="utf-8")
