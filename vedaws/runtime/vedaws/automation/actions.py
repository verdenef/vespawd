"""Execute automation actions against runtime services."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

from vedaws.automation.model import (
    ACTION_EXECUTE_WORKER,
    ACTION_PLUGIN_COMMAND,
    ACTION_PUBLISH_EVENT,
    ACTION_TRANSITION_STATE,
    ACTION_WORKFLOW_STEP,
    RuleAction,
    RuleActionResult,
)
from vedaws.dispatch.dispatcher import WorkerDispatcher
from vedaws.events.bus import EventBus
from vedaws.events.model import Event, create_event
from vedaws.plugins.registry import PluginRegistry
from vedaws.project.detector import sync_manifest_state
from vedaws.project.model import ProjectContext
from vedaws.project.state.states import ProjectState
from vedaws.project.state.triggers import TransitionTrigger
from vedaws.workflow.engine import WorkflowEngine, WorkflowError, parse_task_ref
from vedaws.workflow.models import TaskDefinition
from vedaws.workers.execution import TaskDispatch
from vedaws.workers.registry import WorkerRegistry

logger = logging.getLogger("vedaws.automation")

MAX_AUTOMATION_DEPTH = 5


@dataclass
class ActionContext:
    workspace: Path
    event: Event | None
    project: ProjectContext | None
    dispatcher: WorkerDispatcher | None
    event_bus: EventBus
    worker_registry: WorkerRegistry
    plugin_registry: PluginRegistry
    automation_depth: int = 0
    rule_id: str = ""

    @property
    def workflow_engine(self) -> WorkflowEngine | None:
        if self.project is None:
            return None
        return self.project.workflow_engine


class ActionExecutor:
    """Domain-neutral action runner."""

    def execute(self, action: RuleAction, context: ActionContext) -> RuleActionResult:
        handlers = {
            ACTION_EXECUTE_WORKER: self._execute_worker,
            ACTION_PUBLISH_EVENT: self._publish_event,
            ACTION_TRANSITION_STATE: self._transition_state,
            ACTION_WORKFLOW_STEP: self._workflow_step,
            ACTION_PLUGIN_COMMAND: self._plugin_command,
        }
        handler = handlers.get(action.type)
        if handler is None:
            return RuleActionResult(
                rule_id=context.rule_id,
                action_type=action.type,
                success=False,
                message=f"Unknown action type '{action.type}'",
            )
        try:
            return handler(action, context)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Automation action %s failed", action.type)
            return RuleActionResult(
                rule_id=context.rule_id,
                action_type=action.type,
                success=False,
                message=str(exc),
            )

    def _execute_worker(self, action: RuleAction, context: ActionContext) -> RuleActionResult:
        worker_id = str(action.params.get("worker_id", "")).strip()
        if not worker_id:
            return RuleActionResult(
                context.rule_id,
                ACTION_EXECUTE_WORKER,
                False,
                "execute_worker requires worker_id",
            )

        task_ref = action.params.get("task_ref")
        if task_ref and context.dispatcher is not None:
            workflow_id, task_id = parse_task_ref(str(task_ref))
            result = context.dispatcher.dispatch_and_execute(
                workflow_id,
                task_id,
                worker_id=worker_id,
            )
            if context.project is not None:
                sync_manifest_state(context.project.root, context.project.state_engine)
            success = result.success is not False and result.status.value not in {
                "error",
                "incompatible",
                "no_worker",
            }
            return RuleActionResult(
                context.rule_id,
                ACTION_EXECUTE_WORKER,
                success,
                result.message or result.status.value,
            )

        worker = context.worker_registry.get(worker_id)
        if worker is None or not worker.is_executable:
            return RuleActionResult(
                context.rule_id,
                ACTION_EXECUTE_WORKER,
                False,
                f"Worker '{worker_id}' not found or not executable",
            )

        placeholder = TaskDefinition(id="_automation", name="Automation", capability="")
        dispatch = TaskDispatch(
            workflow_id="_automation",
            task_id="_automation",
            task=placeholder,
            project_name=context.project.name if context.project else "",
            instructions=str(context.workspace),
        )
        outcome = worker.execute(dispatch)
        return RuleActionResult(
            context.rule_id,
            ACTION_EXECUTE_WORKER,
            outcome.status.is_success,
            outcome.message,
        )

    def _publish_event(self, action: RuleAction, context: ActionContext) -> RuleActionResult:
        event_type = str(action.params.get("event_type", "")).strip()
        if not event_type:
            return RuleActionResult(
                context.rule_id,
                ACTION_PUBLISH_EVENT,
                False,
                "publish_event requires event_type",
            )
        if context.automation_depth >= MAX_AUTOMATION_DEPTH:
            return RuleActionResult(
                context.rule_id,
                ACTION_PUBLISH_EVENT,
                False,
                f"Automation depth limit ({MAX_AUTOMATION_DEPTH}) reached",
            )
        payload = action.params.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        context.event_bus.publish(
            create_event(
                event_type,
                source="automation-engine",
                payload=payload,
                correlation_id=context.event.id if context.event else None,
                metadata={
                    "automation_generated": True,
                    "automation_depth": context.automation_depth + 1,
                    "automation_rule_id": context.rule_id,
                },
            )
        )
        return RuleActionResult(
            context.rule_id,
            ACTION_PUBLISH_EVENT,
            True,
            f"Published {event_type}",
        )

    def _transition_state(self, action: RuleAction, context: ActionContext) -> RuleActionResult:
        if context.project is None:
            return RuleActionResult(
                context.rule_id,
                ACTION_TRANSITION_STATE,
                False,
                "No project loaded",
            )
        target_name = str(action.params.get("state", "")).strip()
        target = ProjectState.parse(target_name)
        if target is None:
            return RuleActionResult(
                context.rule_id,
                ACTION_TRANSITION_STATE,
                False,
                f"Invalid state '{target_name}'",
            )
        engine = context.project.state_engine
        reason = str(action.params.get("reason", f"Automation rule '{context.rule_id}'"))
        trigger_name = str(action.params.get("trigger", TransitionTrigger.AUTOMATION.value))
        trigger = TransitionTrigger.parse(trigger_name) or TransitionTrigger.AUTOMATION
        try:
            engine.transition(target, trigger, reason)
            sync_manifest_state(context.project.root, engine)
        except Exception as exc:  # noqa: BLE001
            return RuleActionResult(
                context.rule_id,
                ACTION_TRANSITION_STATE,
                False,
                str(exc),
            )
        return RuleActionResult(
            context.rule_id,
            ACTION_TRANSITION_STATE,
            True,
            f"Transitioned to {target.value}",
        )

    def _workflow_step(self, action: RuleAction, context: ActionContext) -> RuleActionResult:
        engine = context.workflow_engine
        if engine is None:
            return RuleActionResult(
                context.rule_id,
                ACTION_WORKFLOW_STEP,
                False,
                "Workflow engine not available",
            )
        step = str(action.params.get("step", "dispatch")).strip().lower()
        task_ref = str(action.params.get("task_ref", "")).strip()
        if not task_ref:
            return RuleActionResult(
                context.rule_id,
                ACTION_WORKFLOW_STEP,
                False,
                "workflow_step requires task_ref",
            )
        try:
            workflow_id, task_id = parse_task_ref(task_ref)
        except WorkflowError as exc:
            return RuleActionResult(
                context.rule_id,
                ACTION_WORKFLOW_STEP,
                False,
                str(exc),
            )

        if step in {"complete", "complete_task"}:
            engine.complete_task(workflow_id, task_id)
            if context.project is not None:
                sync_manifest_state(context.project.root, context.project.state_engine)
            return RuleActionResult(
                context.rule_id,
                ACTION_WORKFLOW_STEP,
                True,
                f"Completed {task_ref}",
            )
        if step in {"fail", "fail_task"}:
            engine.fail_task(workflow_id, task_id)
            if context.project is not None:
                sync_manifest_state(context.project.root, context.project.state_engine)
            return RuleActionResult(
                context.rule_id,
                ACTION_WORKFLOW_STEP,
                True,
                f"Failed {task_ref}",
            )

        if context.dispatcher is None:
            return RuleActionResult(
                context.rule_id,
                ACTION_WORKFLOW_STEP,
                False,
                "Dispatcher not available",
            )
        worker_id = action.params.get("worker_id")
        result = context.dispatcher.dispatch_and_execute(
            workflow_id,
            task_id,
            worker_id=str(worker_id) if worker_id else None,
        )
        if context.project is not None:
            sync_manifest_state(context.project.root, context.project.state_engine)
        success = result.success is not False and result.status.value not in {
            "error",
            "incompatible",
            "no_worker",
        }
        return RuleActionResult(
            context.rule_id,
            ACTION_WORKFLOW_STEP,
            success,
            result.message or result.status.value,
        )

    def _plugin_command(self, action: RuleAction, context: ActionContext) -> RuleActionResult:
        group = str(action.params.get("group", "")).strip()
        command = str(action.params.get("command", "")).strip()
        if not command:
            return RuleActionResult(
                context.rule_id,
                ACTION_PLUGIN_COMMAND,
                False,
                "plugin_command requires command",
            )
        handler = _find_plugin_command_handler(context.plugin_registry, group, command)
        if handler is None:
            target = f"{group} {command}".strip()
            return RuleActionResult(
                context.rule_id,
                ACTION_PLUGIN_COMMAND,
                False,
                f"Plugin command '{target}' not found",
            )
        args_payload = action.params.get("args", {})
        if not isinstance(args_payload, dict):
            args_payload = {}
        namespace = argparse.Namespace(path=str(context.workspace), **args_payload)
        exit_code = int(handler(namespace))
        return RuleActionResult(
            context.rule_id,
            ACTION_PLUGIN_COMMAND,
            exit_code == 0,
            f"exit code {exit_code}",
        )


def _find_plugin_command_handler(registry: PluginRegistry, group: str, command: str):
    for record in registry.list_active():
        if record.contributions is None:
            continue
        for plugin_command in record.contributions.commands:
            if plugin_command.handler is None:
                continue
            if group:
                if plugin_command.group == group and plugin_command.name == command:
                    return plugin_command.handler
            elif plugin_command.group is None and plugin_command.name == command:
                return plugin_command.handler
    return None
