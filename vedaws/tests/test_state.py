"""Project state machine tests."""

from pathlib import Path

import pytest

from vedaws.project.init import init_project
from vedaws.project.state import (
    InvalidTransitionError,
    ProjectState,
    StateEngine,
    TransitionTrigger,
)
from vedaws.project.state.persistence import load_current_state, load_history


def test_init_creates_state_files(tmp_path: Path) -> None:
    init_project(tmp_path, name="state-demo")
    config_dir = tmp_path / ".vedaws"
    assert (config_dir / "state.toml").is_file()
    assert (config_dir / "transitions.jsonl").is_file()
    assert load_current_state(config_dir) == ProjectState.CREATED
    assert len(load_history(config_dir)) == 1


def test_valid_transition_updates_persistence(tmp_path: Path) -> None:
    init_project(tmp_path)
    engine = StateEngine.load(tmp_path / ".vedaws")
    engine.transition(ProjectState.INITIALIZED, TransitionTrigger.HUMAN_DECISION, "setup")
    assert engine.current == ProjectState.INITIALIZED
    assert load_current_state(tmp_path / ".vedaws") == ProjectState.INITIALIZED
    assert len(engine.history) == 2


def test_invalid_transition_rejected(tmp_path: Path) -> None:
    init_project(tmp_path)
    engine = StateEngine.load(tmp_path / ".vedaws")
    with pytest.raises(InvalidTransitionError):
        engine.transition(ProjectState.EXECUTING, TransitionTrigger.HUMAN_DECISION)
    assert engine.current == ProjectState.CREATED


def test_state_restored_on_reload(tmp_path: Path) -> None:
    init_project(tmp_path)
    engine = StateEngine.load(tmp_path / ".vedaws")
    engine.transition(ProjectState.INITIALIZED, TransitionTrigger.SYSTEM)
    engine.transition(ProjectState.PLANNING, TransitionTrigger.WORKFLOW_RULE)

    reloaded = StateEngine.load(tmp_path / ".vedaws")
    assert reloaded.current == ProjectState.PLANNING
    assert len(reloaded.history) == 3


def test_transition_listener_called(tmp_path: Path) -> None:
    init_project(tmp_path)
    engine = StateEngine.load(tmp_path / ".vedaws")
    seen: list[str] = []

    engine.subscribe(lambda record: seen.append(record.new_state))
    engine.transition(ProjectState.INITIALIZED, TransitionTrigger.HUMAN_DECISION)
    assert seen == [ProjectState.INITIALIZED.value]


def test_lifecycle_path_to_executing(tmp_path: Path) -> None:
    init_project(tmp_path)
    engine = StateEngine.load(tmp_path / ".vedaws")
    for target in (
        ProjectState.INITIALIZED,
        ProjectState.PLANNING,
        ProjectState.READY,
        ProjectState.EXECUTING,
    ):
        engine.transition(target, TransitionTrigger.HUMAN_DECISION)
    assert engine.current == ProjectState.EXECUTING
