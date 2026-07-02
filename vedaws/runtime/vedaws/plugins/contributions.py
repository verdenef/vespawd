"""Plugin contribution models."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vedaws.ai.provider import AIProvider
from vedaws.doctor.model import HealthCheckResult
from vedaws.events.model import Event
from vedaws.workers.interface import Worker


@dataclass
class EventSubscription:
    event_type: str
    handler: Callable[[Event], None]
    name: str
    plugin_id: str
    subscription_id: str | None = None


@dataclass(frozen=True)
class PluginProjectTemplate:
    id: str
    name: str
    description: str
    path: Path
    plugin_id: str = ""


@dataclass
class PluginCommand:
    name: str
    description: str
    handler: Callable[..., int] | None = None
    group: str | None = None
    plugin_id: str = ""


@dataclass
class PluginSkill:
    id: str
    name: str
    description: str = ""


@dataclass
class PluginContributions:
    workers: list[Worker] = field(default_factory=list)
    commands: list[PluginCommand] = field(default_factory=list)
    workflow_templates: list[Path] = field(default_factory=list)
    project_templates: list[PluginProjectTemplate] = field(default_factory=list)
    skills: list[PluginSkill] = field(default_factory=list)
    health_checks: list[Callable[[], HealthCheckResult]] = field(default_factory=list)
    event_subscriptions: list[EventSubscription] = field(default_factory=list)
    configuration: dict[str, Any] = field(default_factory=dict)
    automation_rules: list[Any] = field(default_factory=list)
    ai_providers: list[AIProvider] = field(default_factory=list)

    def merge(self, other: PluginContributions) -> None:
        self.workers.extend(other.workers)
        self.commands.extend(other.commands)
        self.workflow_templates.extend(other.workflow_templates)
        self.project_templates.extend(other.project_templates)
        self.skills.extend(other.skills)
        self.health_checks.extend(other.health_checks)
        self.event_subscriptions.extend(other.event_subscriptions)
        self.configuration.update(other.configuration)
        self.automation_rules.extend(other.automation_rules)
        self.ai_providers.extend(other.ai_providers)
