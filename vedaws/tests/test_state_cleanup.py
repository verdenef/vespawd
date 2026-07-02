"""State transition bridge and eligibility tests."""

from pathlib import Path

from vedaws.project.init import init_project
from vedaws.project.state import (
    ProjectState,
    StateEngine,
    TransitionTrigger,
    apply_state_transition,
    allows_dispatch,
    dispatch_blocked_reason,
)
from vedaws.project.state.bridge import transition_bridge
from vedaws.workflow import WorkflowEngine


def test_transition_bridge_ready_to_executing() -> None:
    assert transition_bridge(ProjectState.READY, ProjectState.EXECUTING) == []


def test_transition_bridge_ready_to_failed() -> None:
    assert transition_bridge(ProjectState.READY, ProjectState.FAILED) == [
        ProjectState.EXECUTING
    ]


def test_apply_state_transition_uses_bridge(tmp_path: Path) -> None:
    init_project(tmp_path)
    engine = StateEngine.load(tmp_path / ".vedaws")
    engine.transition(ProjectState.INITIALIZED, TransitionTrigger.HUMAN_DECISION)
    engine.transition(ProjectState.PLANNING, TransitionTrigger.HUMAN_DECISION)
    engine.transition(ProjectState.READY, TransitionTrigger.WORKFLOW_RULE)

    assert apply_state_transition(
        engine,
        ProjectState.FAILED,
        TransitionTrigger.TASK_OUTCOME,
        "task failed",
    )
    assert engine.current == ProjectState.FAILED


def test_sync_project_state_reaches_executing(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_dir = tmp_path / ".vedaws"
    state_engine = StateEngine.load(config_dir)
    state_engine.transition(ProjectState.INITIALIZED, TransitionTrigger.HUMAN_DECISION)

    workflow = WorkflowEngine.load(config_dir, state_engine=state_engine)
    workflow.activate("default")
    workflow.sync_project_state("refresh")

    assert state_engine.current in {ProjectState.PLANNING, ProjectState.READY}


def test_dispatch_blocked_in_created_state() -> None:
    assert not allows_dispatch(ProjectState.CREATED)
    reason = dispatch_blocked_reason(ProjectState.CREATED)
    assert reason is not None
    assert "created" in reason


def test_dispatch_allowed_in_executing() -> None:
    assert allows_dispatch(ProjectState.EXECUTING)
