"""Plugin SDK — base class and contribution context."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any

from vedaws.ai.provider import AIProvider
from vedaws.automation.model import AutomationRule
from vedaws.doctor.model import HealthCheckResult
from vedaws.events.model import Event
from vedaws.plugins.contributions import (
    EventSubscription,
    PluginCommand,
    PluginContributions,
    PluginProjectTemplate,
    PluginSkill,
)
from vedaws.plugins.manifest import PluginManifest
from vedaws.workers.interface import Worker


class PluginContext:
    """Context passed to plugins during registration."""

    def __init__(self, manifest: PluginManifest) -> None:
        self.manifest = manifest
        self._contributions = PluginContributions()

    @property
    def contributions(self) -> PluginContributions:
        return self._contributions

    @property
    def plugin_id(self) -> str:
        return self.manifest.id

    @property
    def plugin_root(self) -> Path | None:
        return self.manifest.path

    def contribute_worker(self, worker: Worker) -> None:
        self._contributions.workers.append(worker)

    def contribute_command(
        self,
        name: str,
        description: str = "",
        *,
        group: str | None = None,
        handler: Callable[..., int] | None = None,
    ) -> None:
        self._contributions.commands.append(
            PluginCommand(
                name=name,
                description=description,
                handler=handler,
                group=group,
                plugin_id=self.plugin_id,
            )
        )

    def contribute_workflow_template(self, path: Path | str) -> None:
        self._contributions.workflow_templates.append(Path(path))

    def contribute_project_template(
        self,
        template_id: str,
        name: str,
        path: Path | str,
        *,
        description: str = "",
    ) -> None:
        self._contributions.project_templates.append(
            PluginProjectTemplate(
                id=template_id,
                name=name,
                description=description,
                path=Path(path),
                plugin_id=self.plugin_id,
            )
        )

    def contribute_skill(self, skill_id: str, name: str, description: str = "") -> None:
        self._contributions.skills.append(
            PluginSkill(id=skill_id, name=name, description=description)
        )

    def contribute_health_check(
        self, check: Callable[[], HealthCheckResult]
    ) -> None:
        self._contributions.health_checks.append(check)

    def contribute_configuration(self, schema: dict[str, Any]) -> None:
        self._contributions.configuration.update(schema)

    def contribute_automation_rule(self, rule: AutomationRule) -> None:
        """Contribute a data-driven automation rule."""
        enriched = AutomationRule(
            id=rule.id,
            on_event=rule.on_event,
            actions=rule.actions,
            description=rule.description,
            conditions=rule.conditions,
            enabled=rule.enabled,
            source="plugin",
            plugin_id=self.plugin_id,
        )
        self._contributions.automation_rules.append(enriched)

    def contribute_ai_provider(self, provider: AIProvider) -> None:
        """Contribute an AI provider implementation."""
        self._contributions.ai_providers.append(provider)

    def subscribe_event(
        self,
        event_type: str,
        handler: Callable[[Event], None],
        *,
        name: str = "",
    ) -> None:
        """Subscribe to runtime events (registered after plugin activation)."""
        self._contributions.event_subscriptions.append(
            EventSubscription(
                event_type=event_type,
                handler=handler,
                name=name or event_type,
                plugin_id=self.plugin_id,
            )
        )


class VedawsPlugin(ABC):
    """Base class for Vedaws plugins."""

    @abstractmethod
    def register(self, context: PluginContext) -> None:
        """Register plugin contributions with the runtime."""

    def on_load(self) -> None:
        """Called after the plugin module is loaded."""

    def on_unload(self) -> None:
        """Called before the plugin is unloaded."""
