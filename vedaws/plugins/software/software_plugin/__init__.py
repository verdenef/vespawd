"""Software Workflow plugin — first domain plugin for Vedaws."""

from __future__ import annotations

import logging
from pathlib import Path

from software_plugin import commands
from software_plugin.artifacts import SOFTWARE_WORKFLOW_ID, TASK_ARTIFACT_MAP
from software_plugin.workers import all_software_workers
from vedaws.automation.model import AutomationRule, RuleAction, RuleCondition
from vedaws.doctor.model import CheckStatus, HealthCheckResult
from vedaws.events.model import Event
from vedaws.events.types import EventType
from vedaws.plugins.sdk import PluginContext, VedawsPlugin

logger = logging.getLogger("vedaws.plugin.software")

SKILLS: tuple[tuple[str, str, str], ...] = (
    ("software.scoping", "Software scoping", "Clarify goals, constraints, and success criteria"),
    ("software.architecture", "Architecture", "System structure and component boundaries"),
    ("software.api-design", "API design", "Interface contracts and integration design"),
    ("software.implementation", "Implementation", "Build software to specification"),
    ("software.testing", "Testing", "Verification and quality assurance"),
    ("software.review", "Code review", "Structured review before handoff"),
    ("software.handoff", "Handoff", "Operational packaging and knowledge transfer"),
)


class SoftwarePlugin(VedawsPlugin):
    """PAWS successor — software development lifecycle on the Vedaws platform."""

    def register(self, context: PluginContext) -> None:
        for worker in all_software_workers():
            context.contribute_worker(worker)

        if context.plugin_root is not None:
            template_root = context.plugin_root / "templates" / "project"
            context.contribute_project_template(
                "software",
                "Software Development",
                template_root,
                description="Software lifecycle workflow with standard artifacts",
            )
            workflow_template = template_root / "workflows" / "software.workflow.toml"
            if workflow_template.is_file():
                context.contribute_workflow_template(workflow_template)

        for skill_id, name, description in SKILLS:
            context.contribute_skill(skill_id, name, description)

        context.contribute_health_check(self._check_software_plugin)
        context.contribute_health_check(self._check_software_workers)

        context.contribute_command(
            "status",
            "Show software project status, artifacts, and workflow progress",
            group="software",
            handler=commands.cmd_status,
        )
        context.contribute_command(
            "artifacts",
            "List software artifact paths and presence",
            group="software",
            handler=commands.cmd_artifacts,
        )
        context.contribute_command(
            "workflow",
            "Show the software development workflow",
            group="software",
            handler=commands.cmd_workflow,
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

        context.contribute_automation_rule(
            AutomationRule(
                id="software.implement-git-status",
                description="Run git status after the implement task completes",
                on_event=EventType.TASK_COMPLETED,
                conditions=RuleCondition.from_mapping(
                    {"task_id": "implement", "workflow_id": SOFTWARE_WORKFLOW_ID}
                ),
                actions=(
                    RuleAction(
                        type="execute_worker",
                        params={"worker_id": "git.status"},
                    ),
                ),
            )
        )

        context.contribute_configuration(
            {
                "software": {
                    "workflow_id": {
                        "type": "string",
                        "default": SOFTWARE_WORKFLOW_ID,
                        "description": "Default software workflow id",
                    },
                    "artifacts_root": {
                        "type": "string",
                        "default": "docs",
                        "description": "Root directory for software artifacts",
                    },
                }
            }
        )

    def _check_software_plugin(self) -> HealthCheckResult:
        return HealthCheckResult(
            "software plugin",
            CheckStatus.PASS,
            "Software Workflow plugin loaded",
        )

    def _check_software_workers(self) -> HealthCheckResult:
        worker_ids = [worker.id for worker in all_software_workers()]
        return HealthCheckResult(
            "software workers",
            CheckStatus.PASS,
            f"{len(worker_ids)} software worker(s): {', '.join(worker_ids)}",
        )

    def _on_task_completed(self, event: Event) -> None:
        if event.payload.get("workflow_id") != SOFTWARE_WORKFLOW_ID:
            return
        task_id = str(event.payload.get("task_id", ""))
        artifact = TASK_ARTIFACT_MAP.get(task_id)
        logger.debug(
            "Software task completed: %s (artifact=%s)",
            task_id,
            artifact,
        )

    def _on_workflow_completed(self, event: Event) -> None:
        if event.payload.get("workflow_id") != SOFTWARE_WORKFLOW_ID:
            return
        logger.info("Software workflow completed for project")
