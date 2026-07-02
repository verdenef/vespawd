"""Automation rule validation for diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from vedaws.automation.model import (
    ACTION_EXECUTE_WORKER,
    ACTION_PLUGIN_COMMAND,
    ACTION_PUBLISH_EVENT,
    ACTION_TRANSITION_STATE,
    ACTION_WORKFLOW_STEP,
    KNOWN_ACTION_TYPES,
    AutomationRule,
)
from vedaws.project.state.states import ProjectState
from vedaws.workflow.engine import WorkflowError, parse_task_ref

if TYPE_CHECKING:
    from vedaws.plugins.registry import PluginRegistry
    from vedaws.workers.registry import WorkerRegistry


@dataclass
class AutomationValidationIssue:
    rule_id: str
    message: str
    severity: str = "error"


@dataclass
class AutomationValidationReport:
    issues: list[AutomationValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")


def validate_rules(
    rules: list[AutomationRule],
    *,
    worker_registry: WorkerRegistry | None = None,
    plugin_registry: PluginRegistry | None = None,
) -> AutomationValidationReport:
    report = AutomationValidationReport()
    seen_ids: set[str] = set()

    for rule in rules:
        if rule.id in seen_ids:
            report.issues.append(
                AutomationValidationIssue(rule.id, "Duplicate rule id", "error")
            )
        seen_ids.add(rule.id)

        if not rule.on_event:
            report.issues.append(
                AutomationValidationIssue(rule.id, "Missing on_event", "error")
            )
        if not rule.actions:
            report.issues.append(
                AutomationValidationIssue(rule.id, "No actions defined", "warning")
            )
        for action in rule.actions:
            _validate_action(rule, action, report, worker_registry, plugin_registry)

    report.issues.extend(_detect_circular_triggers(rules))
    return report


def _validate_action(
    rule: AutomationRule,
    action,
    report: AutomationValidationReport,
    worker_registry: WorkerRegistry | None,
    plugin_registry: PluginRegistry | None,
) -> None:
    if action.type not in KNOWN_ACTION_TYPES:
        report.issues.append(
            AutomationValidationIssue(
                rule.id,
                f"Unknown action type '{action.type}'",
                "error",
            )
        )
        return

    if action.type == ACTION_EXECUTE_WORKER:
        worker_id = str(action.params.get("worker_id", "")).strip()
        if not worker_id:
            report.issues.append(
                AutomationValidationIssue(rule.id, "execute_worker missing worker_id", "error")
            )
        elif worker_registry is not None and worker_registry.get(worker_id) is None:
            report.issues.append(
                AutomationValidationIssue(
                    rule.id,
                    f"Worker '{worker_id}' not registered",
                    "warning",
                )
            )

    elif action.type == ACTION_PUBLISH_EVENT:
        event_type = str(action.params.get("event_type", "")).strip()
        if not event_type:
            report.issues.append(
                AutomationValidationIssue(rule.id, "publish_event missing event_type", "error")
            )

    elif action.type == ACTION_TRANSITION_STATE:
        state_name = str(action.params.get("state", "")).strip()
        if ProjectState.parse(state_name) is None:
            report.issues.append(
                AutomationValidationIssue(
                    rule.id,
                    f"Invalid transition state '{state_name}'",
                    "error",
                )
            )

    elif action.type == ACTION_WORKFLOW_STEP:
        task_ref = str(action.params.get("task_ref", "")).strip()
        if not task_ref:
            report.issues.append(
                AutomationValidationIssue(rule.id, "workflow_step missing task_ref", "error")
            )
        else:
            try:
                parse_task_ref(task_ref)
            except WorkflowError as exc:
                report.issues.append(
                    AutomationValidationIssue(rule.id, str(exc), "error")
                )

    elif action.type == ACTION_PLUGIN_COMMAND:
        command = str(action.params.get("command", "")).strip()
        if not command:
            report.issues.append(
                AutomationValidationIssue(rule.id, "plugin_command missing command", "error")
            )
        elif plugin_registry is not None:
            group = str(action.params.get("group", "")).strip()
            if not _plugin_command_exists(plugin_registry, group, command):
                target = f"{group} {command}".strip()
                report.issues.append(
                    AutomationValidationIssue(
                        rule.id,
                        f"Plugin command '{target}' not found",
                        "warning",
                    )
                )


def _plugin_command_exists(registry: PluginRegistry, group: str, command: str) -> bool:
    for record in registry.list_active():
        if record.contributions is None:
            continue
        for plugin_command in record.contributions.commands:
            if group:
                if plugin_command.group == group and plugin_command.name == command:
                    return True
            elif plugin_command.group is None and plugin_command.name == command:
                return True
    return False


def _detect_circular_triggers(rules: list[AutomationRule]) -> list[AutomationValidationIssue]:
    """Detect static event cycles introduced by publish_event actions."""
    publishes: dict[str, set[str]] = {}
    listens: dict[str, set[str]] = {}

    for rule in rules:
        listens.setdefault(rule.on_event, set()).add(rule.id)
        for action in rule.actions:
            if action.type != ACTION_PUBLISH_EVENT:
                continue
            event_type = str(action.params.get("event_type", "")).strip()
            if not event_type:
                continue
            publishes.setdefault(rule.id, set()).add(event_type)

    issues: list[AutomationValidationIssue] = []
    for start_rule in rules:
        visited_events: set[str] = set()
        stack = list(publishes.get(start_rule.id, set()))
        while stack:
            event_type = stack.pop()
            if event_type in visited_events:
                issues.append(
                    AutomationValidationIssue(
                        start_rule.id,
                        f"Circular trigger detected via event '{event_type}'",
                        "warning",
                    )
                )
                break
            visited_events.add(event_type)
            for downstream_rule_id in listens.get(event_type, set()):
                stack.extend(publishes.get(downstream_rule_id, set()))
    return issues
