"""Project package."""

from vedaws.project.model import ProjectContext
from vedaws.project.state import (
    InvalidTransitionError,
    ProjectState,
    StateEngine,
    StateValidationError,
    TransitionRecord,
    TransitionTrigger,
)

__all__ = [
    "InvalidTransitionError",
    "ProjectContext",
    "ProjectState",
    "StateEngine",
    "StateValidationError",
    "TransitionRecord",
    "TransitionTrigger",
    "detect_project",
    "init_project",
]


def detect_project(*args, **kwargs):
    """Lazily import project detection to avoid package import cycles."""
    from vedaws.project.detector import detect_project as _detect_project

    return _detect_project(*args, **kwargs)


def init_project(*args, **kwargs):
    """Lazily import project initialization to avoid package import cycles."""
    from vedaws.project.init import init_project as _init_project

    return _init_project(*args, **kwargs)
