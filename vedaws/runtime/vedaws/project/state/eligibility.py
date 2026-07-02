"""Orchestration eligibility rules aligned with design/006_STATE_MACHINE.md."""

from __future__ import annotations

from vedaws.project.state.states import ProjectState

# States where worker dispatch may proceed (possibly after promotion to executing).
_DISPATCH_ALLOWED = frozenset({
    ProjectState.PLANNING,
    ProjectState.READY,
    ProjectState.EXECUTING,
    ProjectState.RECOVERING,
})

# States where workflow tracking and manual task outcome recording are permitted.
_ORCHESTRATION_ALLOWED = frozenset({
    ProjectState.PLANNING,
    ProjectState.READY,
    ProjectState.EXECUTING,
    ProjectState.AWAITING_APPROVAL,
    ProjectState.RECOVERING,
})


def allows_orchestration(state: ProjectState) -> bool:
    return state in _ORCHESTRATION_ALLOWED


def allows_dispatch(state: ProjectState) -> bool:
    """Return whether worker dispatch may begin from this project state."""
    return state in _DISPATCH_ALLOWED


def dispatch_blocked_reason(state: ProjectState) -> str | None:
    if allows_dispatch(state):
        return None
    return (
        f"Project state '{state.value}' does not allow task dispatch — "
        "transition to planning or executing first"
    )
