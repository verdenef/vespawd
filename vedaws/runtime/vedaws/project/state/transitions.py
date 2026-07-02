"""Valid project state transitions."""

from __future__ import annotations

from vedaws.project.state.states import ProjectState

VALID_TRANSITIONS: dict[ProjectState, frozenset[ProjectState]] = {
    ProjectState.CREATED: frozenset({ProjectState.INITIALIZED}),
    ProjectState.INITIALIZED: frozenset({ProjectState.PLANNING}),
    ProjectState.PLANNING: frozenset({ProjectState.READY, ProjectState.BLOCKED}),
    ProjectState.READY: frozenset({ProjectState.EXECUTING, ProjectState.PLANNING}),
    ProjectState.EXECUTING: frozenset({
        ProjectState.AWAITING_APPROVAL,
        ProjectState.BLOCKED,
        ProjectState.FAILED,
        ProjectState.COMPLETED,
        ProjectState.RECOVERING,
        ProjectState.READY,
    }),
    ProjectState.AWAITING_APPROVAL: frozenset({
        ProjectState.EXECUTING,
        ProjectState.BLOCKED,
        ProjectState.FAILED,
        ProjectState.RECOVERING,
    }),
    ProjectState.BLOCKED: frozenset({
        ProjectState.RECOVERING,
        ProjectState.EXECUTING,
        ProjectState.READY,
        ProjectState.PLANNING,
        ProjectState.FAILED,
        ProjectState.ARCHIVED,
    }),
    ProjectState.FAILED: frozenset({
        ProjectState.RECOVERING,
        ProjectState.PLANNING,
        ProjectState.ARCHIVED,
    }),
    ProjectState.RECOVERING: frozenset({
        ProjectState.EXECUTING,
        ProjectState.READY,
        ProjectState.BLOCKED,
        ProjectState.FAILED,
    }),
    ProjectState.COMPLETED: frozenset({ProjectState.ARCHIVED, ProjectState.EXECUTING}),
    ProjectState.ARCHIVED: frozenset({ProjectState.INITIALIZED}),
}


def is_valid_transition(from_state: ProjectState, to_state: ProjectState) -> bool:
    allowed = VALID_TRANSITIONS.get(from_state, frozenset())
    return to_state in allowed


def allowed_targets(from_state: ProjectState) -> frozenset[ProjectState]:
    return VALID_TRANSITIONS.get(from_state, frozenset())
