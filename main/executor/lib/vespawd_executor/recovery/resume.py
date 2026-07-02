"""Resume mid-phase state reader (Executor Spec §12.3).

On a new session the Executor MUST read current_task.md, status.md, and
project_context.md before any code. This module reads those artifacts (read-only)
and reports whether a phase is resumable without re-ingesting the Master Prompt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from vespawd_executor.paths.resolver import WorkspacePaths, parse_project_context

_STATUS_RE = re.compile(r"(?m)^\*\*Status:\*\*\s*`?([^`\n]*)`?\s*$")
_GOAL_RE = re.compile(r"(?ms)^## Goal\s*\n\s*(.+?)(?=^## |\Z)")


@dataclass
class ResumeState:
    resumable: bool = False
    task_status: str = ""
    task_goal: str = ""
    product_name: str | None = None
    has_current_task: bool = False
    has_status: bool = False
    has_project_context: bool = False
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "resumable": self.resumable,
            "task_status": self.task_status,
            "task_goal": self.task_goal,
            "product_name": self.product_name,
            "has_current_task": self.has_current_task,
            "has_status": self.has_status,
            "has_project_context": self.has_project_context,
            "warnings": list(self.warnings),
        }


def read_resume_state(paths: WorkspacePaths) -> ResumeState:
    """Read PAWS memory required before resuming mid-phase (§12.3). Read-only."""
    state = ResumeState()

    ct_path = paths.current_task_path
    if ct_path.is_file():
        state.has_current_task = True
        text = ct_path.read_text(encoding="utf-8", errors="replace")
        status_match = _STATUS_RE.search(text)
        if status_match:
            state.task_status = status_match.group(1).strip()
        goal_match = _GOAL_RE.search(text)
        if goal_match:
            state.task_goal = goal_match.group(1).strip().splitlines()[0].strip()
    else:
        state.warnings.append("current_task.md missing; cannot resume without Master Prompt")

    if paths.status_path.is_file():
        state.has_status = True
    else:
        state.warnings.append("status.md missing; run bridge.sync_status")

    if paths.project_context_path.is_file():
        state.has_project_context = True
        ctx = parse_project_context(paths.project_context_path)
        state.product_name = ctx.product_name
    else:
        state.warnings.append("project_context.md missing")

    # Resumable when there is an active (non-idle) task with a goal to continue.
    active = state.task_status.lower() in {"in_progress", "blocked"}
    state.resumable = state.has_current_task and bool(state.task_goal) and active
    return state
