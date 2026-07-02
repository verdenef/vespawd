"""Runtime context — coordination session state."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from vedaws import __version__
from vedaws.config.schema import VedawsConfig
from vedaws.events.bus import EventBus
from vedaws.plugins.platform import PluginPlatform
from vedaws.plugins.registry import PluginRegistry
from vedaws.project.model import ProjectContext
from vedaws.runtime.status import RuntimeStatus
from vedaws.workers.registry import WorkerRegistry

if TYPE_CHECKING:
    from vedaws.ai.service import AIService
    from vedaws.automation.engine import AutomationEngine
    from vedaws.dispatch.dispatcher import WorkerDispatcher


@dataclass
class RuntimeContext:
    config: VedawsConfig
    registry: PluginRegistry
    worker_registry: WorkerRegistry
    project: ProjectContext | None
    dispatcher: WorkerDispatcher | None
    workspace: Path
    status: RuntimeStatus
    version: str = __version__
    plugin_activation_errors: list[str] | None = None
    event_bus: EventBus | None = None
    plugin_platform: PluginPlatform | None = None
    ai_service: AIService | None = None
    automation_engine: AutomationEngine | None = None

    @property
    def plugin_count(self) -> int:
        return self.registry.count

    @property
    def active_plugin_count(self) -> int:
        return self.registry.active_count

    @property
    def worker_count(self) -> int:
        return self.worker_registry.count

    @property
    def is_active(self) -> bool:
        return self.status == RuntimeStatus.ACTIVE
