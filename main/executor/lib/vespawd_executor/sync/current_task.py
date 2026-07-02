"""Write current_task.md from parsed CURRENT TASK (§4.4, §5.2)."""

from __future__ import annotations

import re
from datetime import date

from vespawd_executor.parse.types import CurrentTaskParsed
from vespawd_executor.sync.io import atomic_write

_GOAL_RE = re.compile(r"(?ms)^## Goal\s*\n\s*(.+?)(?=^## |\Z)")
_STARTED_RE = re.compile(r"\*\*Started:\*\*\s*([^\n]+)")
_STATUS_RE = re.compile(r"(?m)^(\*\*Status:\*\*\s*`?)([^`\n]*)(`?\s*)$")


def _format_notes(
    notes: str,
    *,
    instruction_conflicts: list[str],
    phase_hint: str | None,
) -> str:
    lines: list[str] = []
    for line in notes.splitlines():
        stripped = line.strip()
        if stripped:
            lines.append(stripped if stripped.startswith("-") else f"- {stripped}")

    if phase_hint and not any("vedaws phase" in line.lower() for line in lines):
        lines.append(f"- Vedaws phase: software.{phase_hint}")

    for conflict in instruction_conflicts:
        lines.append(f"- Executor note: {conflict}")

    return "\n".join(lines) if lines else "-"


def _resolve_started(path, goal: str, started_at: date | None) -> str:
    if started_at is not None:
        return started_at.isoformat()
    if path.is_file():
        existing = path.read_text(encoding="utf-8", errors="replace")
        goal_match = _GOAL_RE.search(existing)
        started_match = _STARTED_RE.search(existing)
        if (
            goal_match
            and started_match
            and goal_match.group(1).strip() == goal.strip()
            and started_match.group(1).strip() not in {"", "—", "-"}
        ):
            return started_match.group(1).strip()
    return date.today().isoformat()


def render_current_task(
    task: CurrentTaskParsed,
    *,
    instruction_conflicts: list[str] | None = None,
    phase_hint: str | None = None,
    started: str | None = None,
) -> str:
    conflicts = instruction_conflicts or []
    notes_block = _format_notes(
        task.notes,
        instruction_conflicts=conflicts,
        phase_hint=phase_hint,
    )
    constraints_block = task.constraints.strip() or "- None"
    if not constraints_block.startswith("-"):
        constraints_block = "\n".join(
            f"- {line.strip()}" if line.strip() and not line.strip().startswith("-") else line.strip()
            for line in constraints_block.splitlines()
            if line.strip()
        )

    return f"""# Current Task (POS Scheduler)

**Status:** `{task.status}`
**Started:** {started or date.today().isoformat()}
**Owner:** —

## Goal

{task.goal.strip()}

## Constraints

{constraints_block}

## Acceptance Criteria

{task.acceptance_criteria.strip()}

## Notes

{notes_block}

## Progress Log

| Date | Update |
|------|--------|
| {started or date.today().isoformat()} | Master Prompt ingested |
"""


def write_current_task(
    path,
    task: CurrentTaskParsed,
    *,
    instruction_conflicts: list[str] | None = None,
    phase_hint: str | None = None,
    started_at: date | None = None,
) -> str:
    started = _resolve_started(path, task.goal, started_at)
    content = render_current_task(
        task,
        instruction_conflicts=instruction_conflicts,
        phase_hint=phase_hint,
        started=started,
    )
    atomic_write(path, content)
    return str(path)


def set_task_status(path, status: str) -> tuple[str, bool]:
    """Update the `**Status:**` line during close-out (§10.6). Idempotent.

    Returns (path, changed). No-op (changed=False) if already at `status` or file absent.
    """
    if not path.is_file():
        return str(path), False
    text = path.read_text(encoding="utf-8", errors="replace")
    match = _STATUS_RE.search(text)
    if not match:
        return str(path), False
    if match.group(2).strip() == status:
        return str(path), False
    updated = text[: match.start()] + f"**Status:** `{status}`" + text[match.end():]
    atomic_write(path, updated)
    return str(path), True
