"""Runtime bootstrap process."""

from __future__ import annotations

import logging
from pathlib import Path

from vedaws.ai.integration import build_ai_service
from vedaws.automation.config import load_automation_config
from vedaws.automation.engine import AutomationEngine
from vedaws.automation.loader import load_all_rules
from vedaws.automation.registry import AutomationRegistry
from vedaws.config.loader import apply_plugin_configuration, load_config
from vedaws.dispatch.dispatcher import WorkerDispatcher
from vedaws.events.bus import EventBus
from vedaws.events.integration import wire_project_events
from vedaws.logging.setup import setup_logging
from vedaws.plugins.platform import PluginPlatform
from vedaws.project.detector import detect_project
from vedaws.runtime.context import RuntimeContext
from vedaws.runtime.status import RuntimeStatus
from vedaws.workers.discovery import discover_workers
from vedaws.workers.mock import register_mock_workers
from vedaws.workers.registry import WorkerRegistry

logger = logging.getLogger("vedaws.runtime")


def bootstrap(workspace: Path | None = None, *, quiet: bool = False) -> RuntimeContext:
    """Load configuration, initialize logging, discover plugins, and create runtime context."""
    workspace = (workspace or Path.cwd()).resolve()

    config = load_config(workspace)
    if quiet and config.logging.level == "INFO":
        config.logging.level = "WARNING"
    setup_logging(config.logging)

    logger.info("Bootstrapping Vedaws runtime in %s", workspace)

    event_bus = EventBus()

    worker_discovery = discover_workers(config)
    worker_registry = WorkerRegistry(discovery=worker_discovery)
    worker_registry.attach_event_bus(event_bus)
    for worker in worker_discovery.workers:
        worker_registry.register(worker)
    # Built-in executable mocks override manifest-only entries with the same id.
    register_mock_workers(worker_registry)

    plugin_platform = PluginPlatform(config, workspace, event_bus=event_bus)
    plugin_platform.run(worker_registry)
    registry = plugin_platform.registry
    config = apply_plugin_configuration(config, registry.aggregated_contributions.configuration)
    worker_registry.wire_skills(registry.aggregated_contributions.skills)

    project = detect_project(workspace, read_only=True)
    if project is not None:
        wire_project_events(event_bus, project)

    dispatcher: WorkerDispatcher | None = None
    if project is not None and project.workflow_engine is not None:
        dispatcher = WorkerDispatcher(
            project.workflow_engine,
            worker_registry,
            project_name=project.name,
            workspace=workspace,
            event_bus=event_bus,
        )

    ai_service = build_ai_service(registry, config)
    worker_registry.wire_ai_service(ai_service)
    if dispatcher is not None:
        dispatcher.set_ai_service(ai_service)

    context = RuntimeContext(
        config=config,
        registry=registry,
        worker_registry=worker_registry,
        project=project,
        dispatcher=dispatcher,
        workspace=workspace,
        status=RuntimeStatus.ACTIVE,
        plugin_activation_errors=plugin_platform._activation_errors,
        event_bus=event_bus,
        plugin_platform=plugin_platform,
        ai_service=ai_service,
        automation_engine=_build_automation_engine(
            workspace,
            event_bus,
            project,
            dispatcher,
            worker_registry,
            registry,
        ),
    )

    logger.info(
        "Runtime bootstrap complete — status=%s plugins=%d active=%d workers=%d project=%s",
        context.status,
        context.plugin_count,
        context.registry.active_count,
        context.worker_count,
        context.project.name if context.project else "(none)",
    )
    return context


def shutdown(context: RuntimeContext) -> None:
    """Mark the runtime context as stopped and unload active plugins."""
    context.status = RuntimeStatus.STOPPING
    logger.info("Runtime shutting down")
    if context.automation_engine is not None:
        context.automation_engine.detach()
    if context.plugin_platform is not None:
        context.plugin_platform.unload_all()
    else:
        for record in context.registry.list_records():
            if record.instance is not None:
                try:
                    record.instance.on_unload()
                except Exception:  # noqa: BLE001
                    logger.exception("Plugin %s unload failed", record.id)
    context.status = RuntimeStatus.INACTIVE


def _build_automation_engine(
    workspace: Path,
    event_bus: EventBus,
    project,
    dispatcher: WorkerDispatcher | None,
    worker_registry: WorkerRegistry,
    registry,
) -> AutomationEngine | None:
    rules = load_all_rules(
        workspace,
        plugin_contributions=registry.aggregated_contributions,
        config=load_automation_config(workspace),
    )
    automation_registry = AutomationRegistry(rules)
    engine = AutomationEngine(
        automation_registry,
        event_bus,
        workspace=workspace,
        project=project,
        dispatcher=dispatcher,
        worker_registry=worker_registry,
        plugin_registry=registry,
    )
    engine.attach()
    return engine
