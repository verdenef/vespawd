"""Close-out completed task log (Executor Spec §5.4 step 5, §10.6)."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from vespawd_executor.sync.io import atomic_write


def _slug(goal: str, fallback: str = "task") -> str:
    text = goal.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    if not text:
        return fallback
    return "-".join(text.split("-")[:6])


def completed_log_path(completed_dir: Path, goal: str, *, closed_on: date | None = None) -> Path:
    stamp = (closed_on or date.today()).isoformat()
    return completed_dir / f"{stamp}-{_slug(goal)}.md"


def render_completed_log(
    *,
    goal: str,
    outcome: str,
    closed_on: date,
    vedaws_task_id: str = "",
    acceptance: list[str] | None = None,
    changed_paths: list[str] | None = None,
) -> str:
    accept_lines = "\n".join(f"- {item}" for item in (acceptance or [])) or "- (none recorded)"
    changed_lines = (
        "\n".join(f"- {p}" for p in (changed_paths or [])) or "- (none recorded)"
    )
    task_line = vedaws_task_id or "—"
    return f"""# Completed: {goal.strip()}

- **Closed:** {closed_on.isoformat()}
- **Outcome:** {outcome}
- **Vedaws task:** {task_line}

## Acceptance snapshot

{accept_lines}

## Files changed

{changed_lines}
"""


def write_completed_log(
    completed_dir: Path,
    *,
    goal: str,
    outcome: str,
    closed_on: date | None = None,
    vedaws_task_id: str = "",
    acceptance: list[str] | None = None,
    changed_paths: list[str] | None = None,
) -> tuple[str, bool]:
    """Create `tasks/completed/YYYY-MM-DD-slug.md` (§10.6).

    Idempotent: an existing log for the same date+slug is not overwritten.
    Returns (path, created).
    """
    stamp = closed_on or date.today()
    completed_dir.mkdir(parents=True, exist_ok=True)
    path = completed_log_path(completed_dir, goal, closed_on=stamp)
    if path.is_file():
        return str(path), False

    content = render_completed_log(
        goal=goal,
        outcome=outcome,
        closed_on=stamp,
        vedaws_task_id=vedaws_task_id,
        acceptance=acceptance,
        changed_paths=changed_paths,
    )
    atomic_write(path, content)
    return str(path), True
