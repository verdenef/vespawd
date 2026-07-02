"""Project state engine."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from vedaws.project.state.models import InvalidTransitionError, StateValidationError, TransitionRecord
from vedaws.project.state.persistence import (
    append_history,
    initialize_state,
    load_current_state,
    load_history,
    save_current_state,
    state_file_path,
)
from vedaws.project.state.states import ProjectState
from vedaws.project.state.transitions import allowed_targets, is_valid_transition
from vedaws.project.state.triggers import TransitionTrigger

TransitionListener = Callable[[TransitionRecord], None]


class StateEngine:
    """Canonical project state machine with persistence and listener hooks."""

    def __init__(self, project_dir: Path, current: ProjectState) -> None:
        self._project_dir = project_dir
        self._current = current
        self._history: list[TransitionRecord] = load_history(project_dir)
        self._listeners: list[TransitionListener] = []

    @classmethod
    def load(cls, project_dir: Path, *, legacy_state: str | None = None) -> StateEngine:
        fallback = ProjectState.parse(legacy_state) if legacy_state else None

        if not state_file_path(project_dir).is_file():
            initial = fallback or ProjectState.CREATED
            initialize_state(project_dir, initial)

        current = load_current_state(project_dir, fallback=fallback)
        return cls(project_dir, current)

    @property
    def project_dir(self) -> Path:
        return self._project_dir

    @property
    def current(self) -> ProjectState:
        return self._current

    @property
    def history(self) -> list[TransitionRecord]:
        return list(self._history)

    def validate(self) -> None:
        if ProjectState.parse(self._current.value) is None:
            raise StateValidationError(f"Invalid current state: {self._current!r}")

    def allowed_transitions(self) -> frozenset[ProjectState]:
        return allowed_targets(self._current)

    def can_transition_to(self, target: ProjectState) -> bool:
        return is_valid_transition(self._current, target)

    def subscribe(self, listener: TransitionListener) -> None:
        self._listeners.append(listener)

    def transition(
        self,
        target: ProjectState,
        trigger: TransitionTrigger,
        reason: str | None = None,
    ) -> TransitionRecord:
        if not is_valid_transition(self._current, target):
            raise InvalidTransitionError(
                f"Invalid transition: {self._current.value} -> {target.value}"
            )

        previous = self._current
        record = TransitionRecord.create(previous, target, trigger, reason)
        self._current = target
        save_current_state(self._project_dir, target)
        append_history(self._project_dir, record)
        self._history.append(record)
        self._emit(record)
        return record

    def _emit(self, record: TransitionRecord) -> None:
        for listener in self._listeners:
            listener(record)
