"""State CLI output formatting."""

from __future__ import annotations

from vedaws.project.state.engine import StateEngine
from vedaws.project.state.transitions import allowed_targets


def format_current_state(engine: StateEngine, project_name: str) -> str:
    allowed = allowed_targets(engine.current)
    allowed_text = ", ".join(state.value for state in sorted(allowed, key=lambda s: s.value))
    if not allowed_text:
        allowed_text = "(none — terminal or blocked)"

    return "\n".join(
        [
            f"Project:        {project_name}",
            f"Current state:  {engine.current.value}",
            f"Allowed next:   {allowed_text}",
            f"Transitions:    {len(engine.history)} recorded",
        ]
    )


def format_state_history(engine: StateEngine, project_name: str) -> str:
    if not engine.history:
        return f"Project: {project_name}\nNo transitions recorded."

    lines = [
        f"Project: {project_name}",
        f"Current state: {engine.current.value}",
        "",
        f"{'TIMESTAMP':<28} {'FROM':<20} {'TO':<20} {'TRIGGER':<16} REASON",
        "-" * 100,
    ]
    for record in engine.history:
        reason = record.reason or ""
        lines.append(
            f"{record.timestamp:<28} {record.previous_state:<20} {record.new_state:<20} "
            f"{record.trigger:<16} {reason}"
        )
    return "\n".join(lines)
