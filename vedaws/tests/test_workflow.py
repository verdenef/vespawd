"""Workflow and task engine tests."""

from pathlib import Path

import pytest

from vedaws.project.init import init_project
from vedaws.project.state import ProjectState, StateEngine, TransitionTrigger
from vedaws.workflow import InvalidTaskTransitionError, TaskStatus, WorkflowEngine, WorkflowStatus
from vedaws.workflow.manifest import parse_workflow_manifest
from vedaws.workflow.persistence import load_progress, progress_file_path


def test_init_creates_default_workflow(tmp_path: Path) -> None:
    init_project(tmp_path, name="wf-demo")
    workflow_path = tmp_path / ".vedaws" / "workflows" / "default.workflow.toml"
    assert workflow_path.is_file()
    definition, error = parse_workflow_manifest(workflow_path)
    assert error is None
    assert definition is not None
    assert definition.id == "default"
    assert len(definition.tasks) == 3


def test_workflow_engine_loads_definitions(tmp_path: Path) -> None:
    init_project(tmp_path)
    engine = WorkflowEngine.load(tmp_path / ".vedaws")
    workflows = engine.list_workflows()
    assert len(workflows) == 1
    assert workflows[0].id == "default"


def test_activate_initializes_tasks(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_dir = tmp_path / ".vedaws"
    state_engine = StateEngine.load(config_dir)
    state_engine.transition(ProjectState.INITIALIZED, TransitionTrigger.HUMAN_DECISION)

    engine = WorkflowEngine.load(config_dir, state_engine=state_engine)
    engine.activate("default")

    plan = engine.task_registry.get_instance("default", "plan")
    validate = engine.task_registry.get_instance("default", "validate")
    assert plan is not None and plan.status == TaskStatus.READY
    assert validate is not None and validate.status == TaskStatus.PENDING
    progress = engine.progress("default")
    assert progress.status == WorkflowStatus.IN_PROGRESS
    assert progress.ready == 1


def test_activate_transitions_project_to_planning(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_dir = tmp_path / ".vedaws"
    state_engine = StateEngine.load(config_dir)
    state_engine.transition(ProjectState.INITIALIZED, TransitionTrigger.HUMAN_DECISION)

    engine = WorkflowEngine.load(config_dir, state_engine=state_engine)
    engine.activate("default")
    assert state_engine.current in {ProjectState.PLANNING, ProjectState.READY}


def test_complete_task_advances_dependencies(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_dir = tmp_path / ".vedaws"
    state_engine = StateEngine.load(config_dir)
    for target in (ProjectState.INITIALIZED, ProjectState.PLANNING):
        state_engine.transition(target, TransitionTrigger.HUMAN_DECISION)

    engine = WorkflowEngine.load(config_dir, state_engine=state_engine)
    engine.activate("default")
    engine.complete_task("default", "plan")

    validate = engine.task_registry.get_instance("default", "validate")
    assert validate is not None
    assert validate.status == TaskStatus.READY


def test_complete_all_tasks_completes_workflow(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_dir = tmp_path / ".vedaws"
    state_engine = StateEngine.load(config_dir)
    for target in (ProjectState.INITIALIZED, ProjectState.PLANNING):
        state_engine.transition(target, TransitionTrigger.HUMAN_DECISION)

    engine = WorkflowEngine.load(config_dir, state_engine=state_engine)
    engine.activate("default")
    for task_id in ("plan", "validate", "ready"):
        engine.complete_task("default", task_id)

    progress = engine.progress("default")
    assert progress.status == WorkflowStatus.COMPLETED
    assert progress.completed == 3


def test_fail_task_marks_workflow_blocked(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_dir = tmp_path / ".vedaws"
    state_engine = StateEngine.load(config_dir)
    state_engine.transition(ProjectState.INITIALIZED, TransitionTrigger.HUMAN_DECISION)

    engine = WorkflowEngine.load(config_dir, state_engine=state_engine)
    engine.activate("default")
    engine.fail_task("default", "plan")

    plan = engine.task_registry.get_instance("default", "plan")
    assert plan is not None
    assert plan.status == TaskStatus.FAILED
    assert engine.progress("default").status == WorkflowStatus.BLOCKED
    assert state_engine.current == ProjectState.FAILED


def test_progress_persists_across_reload(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_dir = tmp_path / ".vedaws"
    state_engine = StateEngine.load(config_dir)
    state_engine.transition(ProjectState.INITIALIZED, TransitionTrigger.HUMAN_DECISION)

    engine = WorkflowEngine.load(config_dir, state_engine=state_engine)
    engine.activate("default")
    engine.complete_task("default", "plan")
    assert progress_file_path(config_dir).is_file()

    reloaded = WorkflowEngine.load(config_dir, state_engine=state_engine)
    plan = reloaded.task_registry.get_instance("default", "plan")
    assert plan is not None
    assert plan.status == TaskStatus.RECORDED
    workflows, tasks = load_progress(config_dir)
    assert "default" in workflows


def test_complete_requires_ready_status(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_dir = tmp_path / ".vedaws"
    engine = WorkflowEngine.load(config_dir)
    with pytest.raises(InvalidTaskTransitionError):
        engine.complete_task("default", "validate")


def test_parse_workflow_manifest_supports_optional_ai_capability(tmp_path: Path) -> None:
    workflow_path = tmp_path / "ai.workflow.toml"
    workflow_path.write_text(
        """
[workflow]
id = "ai"
name = "AI workflow"

[[tasks]]
id = "implement"
name = "Implement"
capability = "software-implementation"
ai_capability = "implement"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    definition, error = parse_workflow_manifest(workflow_path)
    assert error is None
    assert definition is not None
    assert definition.tasks[0].capability == "software-implementation"
    assert definition.tasks[0].ai_capability == "implement"
