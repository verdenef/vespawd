"""Shared project state transition helpers."""

from __future__ import annotations

from vedaws.project.state.engine import StateEngine
from vedaws.project.state.states import ProjectState
from vedaws.project.state.triggers import TransitionTrigger


def transition_bridge(current: ProjectState, target: ProjectState) -> list[ProjectState]:
    """Intermediate states for transitions not directly allowed by the state machine."""
    if target == ProjectState.FAILED and current in {
        ProjectState.PLANNING,
        ProjectState.READY,
    }:
        return [ProjectState.EXECUTING]
    if target == ProjectState.COMPLETED and current == ProjectState.READY:
        return [ProjectState.EXECUTING]
    if target == ProjectState.AWAITING_APPROVAL and current in {
        ProjectState.PLANNING,
        ProjectState.READY,
    }:
        return [ProjectState.EXECUTING]
    if target == ProjectState.EXECUTING and current in {
        ProjectState.PLANNING,
        ProjectState.READY,
    }:
        return []
    return []


def apply_state_transition(
    engine: StateEngine,
    target: ProjectState,
    trigger: TransitionTrigger,
    reason: str,
) -> bool:
    """Apply a transition with bridge support. Returns True if the target state was reached."""
    if engine.current == target:
        return True
    if engine.can_transition_to(target):
        engine.transition(target, trigger, reason)
        return True
    for bridge in transition_bridge(engine.current, target):
        if engine.can_transition_to(bridge):
            engine.transition(bridge, trigger, reason)
    if engine.can_transition_to(target):
        engine.transition(target, trigger, reason)
        return engine.current == target
    return False
