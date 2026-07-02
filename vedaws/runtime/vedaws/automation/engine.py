"""Automation engine — subscribe to events and execute matching rules."""

from __future__ import annotations

import logging

from vedaws.automation.actions import MAX_AUTOMATION_DEPTH, ActionContext, ActionExecutor
from vedaws.automation.conditions import matches_condition
from vedaws.automation.model import RuleExecutionResult
from vedaws.automation.registry import AutomationRegistry
from vedaws.dispatch.dispatcher import WorkerDispatcher
from vedaws.events.bus import EventBus
from vedaws.events.model import Event, create_event
from vedaws.plugins.registry import PluginRegistry
from vedaws.project.model import ProjectContext
from vedaws.workers.registry import WorkerRegistry

logger = logging.getLogger("vedaws.automation")


class AutomationEngine:
    """Event-driven rule executor owned by the runtime."""

    SUBSCRIBER_PREFIX = "automation-engine"

    def __init__(
        self,
        registry: AutomationRegistry,
        event_bus: EventBus,
        *,
        workspace,
        project: ProjectContext | None,
        dispatcher: WorkerDispatcher | None,
        worker_registry: WorkerRegistry,
        plugin_registry: PluginRegistry,
    ) -> None:
        self._registry = registry
        self._event_bus = event_bus
        self._workspace = workspace
        self._project = project
        self._dispatcher = dispatcher
        self._worker_registry = worker_registry
        self._plugin_registry = plugin_registry
        self._executor = ActionExecutor()
        self._subscription_ids: list[str] = []
        self._active_rule_chain: list[str] = []

    @property
    def registry(self) -> AutomationRegistry:
        return self._registry

    def attach(self) -> None:
        """Subscribe to all event types referenced by registered rules."""
        self.detach()
        event_types = {rule.on_event for rule in self._registry.list_rules()}
        for event_type in sorted(event_types):
            sub_id = self._event_bus.subscribe(
                event_type,
                self._on_event,
                subscriber_id=f"{self.SUBSCRIBER_PREFIX}:{event_type}",
                source="automation-engine",
            )
            self._subscription_ids.append(sub_id)

    def detach(self) -> None:
        for sub_id in list(self._subscription_ids):
            self._event_bus.unsubscribe(sub_id)
        self._subscription_ids.clear()

    def run_rule(self, rule_id: str, event: Event | None = None) -> RuleExecutionResult:
        rule = self._registry.get(rule_id)
        if rule is None:
            return RuleExecutionResult(
                rule_id=rule_id,
                event_type=event.type if event else "",
                matched=False,
                skipped=True,
                skip_reason="Rule not found",
            )
        if not rule.enabled:
            return RuleExecutionResult(
                rule_id=rule_id,
                event_type=event.type if event else rule.on_event,
                matched=False,
                skipped=True,
                skip_reason="Rule disabled",
            )
        if event is not None and event.type != rule.on_event:
            return RuleExecutionResult(
                rule_id=rule_id,
                event_type=event.type,
                matched=False,
                skipped=True,
                skip_reason="Event type mismatch",
            )
        if event is not None and not matches_condition(event, rule.conditions):
            return RuleExecutionResult(
                rule_id=rule_id,
                event_type=event.type,
                matched=False,
                skipped=True,
                skip_reason="Conditions not met",
            )
        synthetic = event or create_event(rule.on_event, source="automation-cli")
        return self._execute_rule(rule, synthetic)

    def run_for_event(self, event: Event) -> list[RuleExecutionResult]:
        if self._should_skip_event(event):
            return []
        results: list[RuleExecutionResult] = []
        for rule in self._registry.rules_for_event(event.type):
            if not rule.enabled:
                continue
            if not matches_condition(event, rule.conditions):
                results.append(
                    RuleExecutionResult(
                        rule_id=rule.id,
                        event_type=event.type,
                        matched=False,
                        skipped=True,
                        skip_reason="Conditions not met",
                    )
                )
                continue
            results.append(self._execute_rule(rule, event))
        return results

    def _on_event(self, event: Event) -> None:
        if self._should_skip_event(event):
            return
        self.run_for_event(event)

    def _should_skip_event(self, event: Event) -> bool:
        depth = int(event.metadata.get("automation_depth", 0))
        if event.metadata.get("automation_generated") and depth >= MAX_AUTOMATION_DEPTH:
            logger.debug("Skipping event %s — automation depth limit", event.type)
            return True
        return False

    def _execute_rule(self, rule, event: Event) -> RuleExecutionResult:
        if rule.id in self._active_rule_chain:
            return RuleExecutionResult(
                rule_id=rule.id,
                event_type=event.type,
                matched=True,
                skipped=True,
                skip_reason="Circular rule execution detected",
            )

        self._active_rule_chain.append(rule.id)
        try:
            depth = int(event.metadata.get("automation_depth", 0))
            context = ActionContext(
                workspace=self._workspace,
                event=event,
                project=self._project,
                dispatcher=self._dispatcher,
                event_bus=self._event_bus,
                worker_registry=self._worker_registry,
                plugin_registry=self._plugin_registry,
                automation_depth=depth,
                rule_id=rule.id,
            )
            action_results = [
                self._executor.execute(action, context) for action in rule.actions
            ]
            logger.info(
                "Automation rule '%s' executed for event %s (%d action(s))",
                rule.id,
                event.type,
                len(action_results),
            )
            return RuleExecutionResult(
                rule_id=rule.id,
                event_type=event.type,
                matched=True,
                action_results=action_results,
            )
        finally:
            if self._active_rule_chain and self._active_rule_chain[-1] == rule.id:
                self._active_rule_chain.pop()
