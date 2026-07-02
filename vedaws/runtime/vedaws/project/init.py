"""Project initialization."""

from __future__ import annotations

from pathlib import Path

from vedaws.config.paths import (
    PROJECT_AUTOMATION_FILE,
    PROJECT_CONFIG_DIR_NAME,
    PROJECT_CONFIG_FILE,
    PROJECT_MANIFEST_FILE,
    PROJECT_PLUGINS_FILE,
)
from vedaws.plugins.activation import default_project_activation, save_activation_config
from vedaws.project.state.models import TransitionRecord
from vedaws.project.state.persistence import append_history, initialize_state
from vedaws.project.state.states import ProjectState
from vedaws.project.state.triggers import TransitionTrigger
from vedaws.project.templates import ProjectTemplate, apply_project_template


def init_project(
    workspace: Path,
    name: str | None = None,
    *,
    template: ProjectTemplate | None = None,
) -> Path:
    workspace = workspace.resolve()
    config_dir = workspace / PROJECT_CONFIG_DIR_NAME
    config_dir.mkdir(parents=True, exist_ok=True)

    project_name = name or workspace.name
    manifest_path = config_dir / PROJECT_MANIFEST_FILE
    config_path = config_dir / PROJECT_CONFIG_FILE

    if manifest_path.exists():
        raise FileExistsError(f"Project already initialized at {config_dir}")

    manifest_path.write_text(
        _project_manifest_template(project_name),
        encoding="utf-8",
    )
    config_path.write_text(_project_config_template(), encoding="utf-8")
    plugins_path = config_dir / PROJECT_PLUGINS_FILE
    save_activation_config(plugins_path, default_project_activation())
    _write_default_workflow(config_dir)
    _write_default_automation(config_dir)

    initialize_state(config_dir, ProjectState.CREATED)
    record = TransitionRecord.create(
        ProjectState.CREATED,
        ProjectState.CREATED,
        TransitionTrigger.SYSTEM,
        "Project initialized",
    )
    append_history(config_dir, record)

    if template is not None:
        apply_project_template(template, workspace, config_dir)

    return config_dir


def _project_manifest_template(name: str) -> str:
    return f"""# Vedaws project manifest

[project]
name = "{name}"
state = "created"
"""


def _project_config_template() -> str:
    return """# Vedaws project configuration

[logging]
level = "INFO"

[plugins]
enabled = true

[workers]
enabled = true

# AI provider routing (capability-based — no provider names in workflows)
# [ai]
# default_provider = "mock-ai"
#
# [ai.capabilities.chat]
# preferred = "mock-ai"
# fallback = ["mock-ai"]
"""


def _write_default_workflow(config_dir: Path) -> None:
    workflows_dir = config_dir / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    default_path = workflows_dir / "default.workflow.toml"
    if default_path.exists():
        return
    default_path.write_text(_default_workflow_template(), encoding="utf-8")


def _default_workflow_template() -> str:
    return """# Default Vedaws workflow — customize or add more *.workflow.toml files

[workflow]
id = "default"
name = "Default workflow"
version = "0.1.0"
description = "Initial project setup and validation tasks."

[[tasks]]
id = "plan"
name = "Plan work"
description = "Structure tasks and dependencies for the project."
capability = "planning"

[[tasks]]
id = "validate"
name = "Validate setup"
description = "Confirm project configuration and runtime health."
depends_on = ["plan"]
capability = "validation"

[[tasks]]
id = "ready"
name = "Mark ready"
description = "Confirm the project is ready for execution."
depends_on = ["validate"]
capability = "review"
"""


def _write_default_automation(config_dir: Path) -> None:
    path = config_dir / PROJECT_AUTOMATION_FILE
    if path.exists():
        return
    path.write_text(_default_automation_template(), encoding="utf-8")


def _default_automation_template() -> str:
    return """# Vedaws automation rules — event-driven reactions
#
# Rules follow: on_event → if (optional) → then (action(s))
#
# [automation]
# enabled = true
#
# [[rules]]
# id = "example-on-task-complete"
# description = "Example reaction to a completed task"
# on_event = "TaskCompleted"
#
# [rules.if]
# task_id = "plan"
#
# [[rules.then]]
# type = "execute_worker"
# worker_id = "mock.success"
"""
