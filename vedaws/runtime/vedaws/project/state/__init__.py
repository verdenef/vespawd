"""Project lifecycle state machine."""

from vedaws.project.state.engine import StateEngine, TransitionListener
from vedaws.project.state.models import InvalidTransitionError, StateValidationError, TransitionRecord
from vedaws.project.state.persistence import HISTORY_FILE_NAME, STATE_FILE_NAME
from vedaws.project.state.states import ProjectState
from vedaws.project.state.bridge import apply_state_transition, transition_bridge
from vedaws.project.state.eligibility import (
    allows_dispatch,
    allows_orchestration,
    dispatch_blocked_reason,
)
from vedaws.project.state.triggers import TransitionTrigger
from vedaws.project.state.transitions import allowed_targets, is_valid_transition

__all__ = [
    "HISTORY_FILE_NAME",
    "STATE_FILE_NAME",
    "InvalidTransitionError",
    "ProjectState",
    "StateEngine",
    "StateValidationError",
    "TransitionListener",
    "TransitionRecord",
    "TransitionTrigger",
    "allowed_targets",
    "allows_dispatch",
    "allows_orchestration",
    "apply_state_transition",
    "dispatch_blocked_reason",
    "is_valid_transition",
    "transition_bridge",
]
