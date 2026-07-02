"""Unity Game Development plugin — multi-domain validation for Vedaws."""

from __future__ import annotations

import logging

from unity_plugin import commands
from unity_plugin.artifacts import (
    TASK_ARTIFACT_MAP,
    UNITY_WORKFLOW_ID,
    layout_is_valid,
)
from unity_plugin.workers import all_unity_workers
from vedaws.doctor.model import CheckStatus, HealthCheckResult
from vedaws.events.model import Event
from vedaws.events.types import EventType
from vedaws.plugins.sdk import PluginContext, VedawsPlugin

logger = logging.getLogger("vedaws.plugin.unity")

SKILLS: tuple[tuple[str, str, str], ...] = (
    ("unity-csharp", "Unity C#", "C# scripting patterns for Unity projects"),
    ("unity-prefabs", "Unity prefabs", "Prefab composition and reuse"),
    ("unity-ui", "Unity UI", "uGUI / UI Toolkit interface design"),
    ("unity-animation", "Unity animation", "Animation clips, timelines, and state machines"),
    ("unity-ai", "Unity AI", "NPC behaviour and navigation placeholders"),
    ("unity-performance", "Unity performance", "Profiling and optimization practices"),
)


class UnityPlugin(VedawsPlugin):
    """Game development domain plugin — no Unity Editor or AI integration."""

    def register(self, context: PluginContext) -> None:
        for worker in all_unity_workers():
            context.contribute_worker(worker)

        if context.plugin_root is not None:
            template_root = context.plugin_root / "templates" / "project"
            context.contribute_project_template(
                "unity",
                "Unity Game Development",
                template_root,
                description="Unity game lifecycle with standard layout and documentation",
            )
            workflow_template = template_root / "workflows" / "unity.workflow.toml"
            if workflow_template.is_file():
                context.contribute_workflow_template(workflow_template)

        for skill_id, name, description in SKILLS:
            context.contribute_skill(skill_id, name, description)

        context.contribute_health_check(self._check_unity_plugin)
        context.contribute_health_check(self._check_unity_workers)
        context.contribute_health_check(self._check_unity_layout)

        context.contribute_command(
            "status",
            "Show Unity project layout, artifacts, and workflow progress",
            group="unity",
            handler=commands.cmd_status,
        )
        context.contribute_command(
            "workflow",
            "Show the Unity game development workflow",
            group="unity",
            handler=commands.cmd_workflow,
        )
        context.contribute_command(
            "build",
            "Stub build command (no Unity Editor integration)",
            group="unity",
            handler=commands.cmd_build,
        )
        context.contribute_command(
            "package",
            "Inspect Unity package manifest placeholder",
            group="unity",
            handler=commands.cmd_package,
        )

        context.subscribe_event(
            EventType.TASK_COMPLETED,
            self._on_task_completed,
            name="artifact-tracker",
        )
        context.subscribe_event(
            EventType.WORKFLOW_COMPLETED,
            self._on_workflow_completed,
            name="workflow-observer",
        )

        context.contribute_configuration(
            {
                "unity": {
                    "workflow_id": {
                        "type": "string",
                        "default": UNITY_WORKFLOW_ID,
                        "description": "Default Unity workflow id",
                    },
                    "docs_root": {
                        "type": "string",
                        "default": "Docs",
                        "description": "Unity documentation root directory",
                    },
                }
            }
        )

    def _check_unity_plugin(self) -> HealthCheckResult:
        return HealthCheckResult(
            "unity plugin",
            CheckStatus.PASS,
            "Unity Game Development plugin loaded",
        )

    def _check_unity_workers(self) -> HealthCheckResult:
        worker_ids = [worker.id for worker in all_unity_workers()]
        return HealthCheckResult(
            "unity workers",
            CheckStatus.PASS,
            f"{len(worker_ids)} Unity worker(s): {', '.join(worker_ids)}",
        )

    def _check_unity_layout(self) -> HealthCheckResult:
        from pathlib import Path

        if layout_is_valid(Path.cwd()):
            return HealthCheckResult(
                "unity project layout",
                CheckStatus.PASS,
                "Unity layout directories present (Assets, Packages, ProjectSettings, Docs)",
            )
        return HealthCheckResult(
            "unity project layout",
            CheckStatus.WARN,
            "Unity layout incomplete — run `vedaws init unity` in a Unity template project",
        )

    def _on_task_completed(self, event: Event) -> None:
        if event.payload.get("workflow_id") != UNITY_WORKFLOW_ID:
            return
        task_id = str(event.payload.get("task_id", ""))
        artifact = TASK_ARTIFACT_MAP.get(task_id)
        logger.debug("Unity task completed: %s (artifact=%s)", task_id, artifact)

    def _on_workflow_completed(self, event: Event) -> None:
        if event.payload.get("workflow_id") != UNITY_WORKFLOW_ID:
            return
        logger.info("Unity workflow completed for project")
