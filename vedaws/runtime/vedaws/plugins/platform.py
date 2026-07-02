"""Plugin platform orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from vedaws.config.schema import VedawsConfig
from vedaws.events.bus import EventBus
from vedaws.events.model import create_event
from vedaws.events.types import EventType
from vedaws.plugins.activation import (
    global_plugins_path,
    load_activation_config,
    merge_activation,
    project_plugins_path,
)
from vedaws.plugins.dependencies import resolve_dependencies
from vedaws.plugins.discovery import PluginDiscoveryResult, discover_plugins
from vedaws.plugins.lifecycle import PluginStatus
from vedaws.plugins.loader import load_plugin_class
from vedaws.plugins.registry import PluginRecord, PluginRegistry
from vedaws.plugins.sdk import PluginContext
from vedaws.plugins.validation import validate_manifest
from vedaws.workers.registry import WorkerRegistry

logger = logging.getLogger("vedaws.plugins")


@dataclass
class PluginPlatformResult:
    registry: PluginRegistry
    activation_errors: list[str] = field(default_factory=list)


class PluginPlatform:
    """Manages the full plugin lifecycle."""

    def __init__(
        self,
        config: VedawsConfig,
        workspace: Path,
        *,
        event_bus: EventBus | None = None,
    ) -> None:
        self._config = config
        self._workspace = workspace
        self._event_bus = event_bus
        self._registry = PluginRegistry()
        self._discovery: PluginDiscoveryResult | None = None
        self._activation_errors: list[str] = []

    @classmethod
    def bootstrap(
        cls,
        config: VedawsConfig,
        workspace: Path,
        worker_registry: WorkerRegistry,
        *,
        event_bus: EventBus | None = None,
    ) -> PluginPlatformResult:
        platform = cls(config, workspace, event_bus=event_bus)
        platform.run(worker_registry)
        return PluginPlatformResult(
            registry=platform.registry,
            activation_errors=platform._activation_errors,
        )

    @property
    def registry(self) -> PluginRegistry:
        return self._registry

    def run(self, worker_registry: WorkerRegistry) -> None:
        self._discover()
        self._validate_all()
        selected = self._select_for_activation()
        resolution = resolve_dependencies(
            {record.manifest.id: record.manifest for record in self._registry.list_records()},
            selected_ids=selected,
        )
        if not resolution.ok:
            self._activation_errors.extend(resolution.errors)
            for plugin_id in selected:
                record = self._registry.get(plugin_id)
                if record is not None:
                    record.status = PluginStatus.FAILED
                    record.error = "; ".join(resolution.errors)
            return

        for plugin_id in resolution.order:
            if plugin_id not in selected:
                continue
            record = self._registry.get(plugin_id)
            if record is None:
                continue
            if not self._load(record):
                continue
            if not self._initialize(record):
                continue
            self._activate(record, worker_registry)

    def _discover(self) -> None:
        self._discovery = discover_plugins(self._config)
        self._registry.discovery = self._discovery
        for manifest in self._discovery.plugins:
            self._registry.register_record(
                PluginRecord(manifest=manifest, status=PluginStatus.DISCOVERED)
            )

    def _validate_all(self) -> None:
        for record in self._registry.list_records():
            if record.status == PluginStatus.DISABLED:
                continue
            errors = validate_manifest(record.manifest)
            if errors:
                record.status = PluginStatus.FAILED
                record.error = "; ".join(errors)
            else:
                record.status = PluginStatus.VALIDATED

    def _select_for_activation(self) -> set[str]:
        global_config = load_activation_config(global_plugins_path())
        project_path = project_plugins_path(self._workspace)
        project_config = (
            load_activation_config(project_path) if project_path is not None else None
        )
        activation = merge_activation(global_config, project_config)

        selected: set[str] = set()
        for record in self._registry.list_records():
            if activation.is_disabled(record.id):
                record.status = PluginStatus.DISABLED
                continue
            if activation.enabled and not activation.is_explicitly_enabled(record.id):
                record.status = PluginStatus.DISCOVERED
                continue
            if record.status == PluginStatus.FAILED:
                continue
            selected.add(record.id)
        return selected

    def _load(self, record: PluginRecord) -> bool:
        if record.status not in {PluginStatus.VALIDATED, PluginStatus.DISCOVERED}:
            return record.status == PluginStatus.LOADED
        plugin_cls, error = load_plugin_class(record.manifest)
        if error or plugin_cls is None:
            record.status = PluginStatus.FAILED
            record.error = error or "failed to load plugin class"
            return False
        record.plugin_class = plugin_cls
        record.status = PluginStatus.LOADED
        return True

    def _initialize(self, record: PluginRecord) -> bool:
        if record.plugin_class is None:
            return False
        try:
            instance = record.plugin_class()
            instance.on_load()
            record.instance = instance
            record.status = PluginStatus.INITIALIZED
            return True
        except Exception as exc:  # noqa: BLE001
            record.status = PluginStatus.FAILED
            record.error = f"initialize failed: {exc}"
            logger.exception("Plugin %s failed to initialize", record.id)
            return False

    def _activate(self, record: PluginRecord, worker_registry: WorkerRegistry) -> None:
        if record.instance is None:
            return
        try:
            context = PluginContext(record.manifest)
            record.instance.register(context)
            record.contributions = context.contributions
            self._registry.merge_contributions(context.contributions)
            for worker in context.contributions.workers:
                worker_registry.register(worker)
            self._register_event_subscriptions(record, context)
            record.status = PluginStatus.ACTIVE
            self._publish_plugin_event(record, EventType.PLUGIN_LOADED)
            logger.info("Plugin '%s' active", record.id)
        except Exception as exc:  # noqa: BLE001
            record.status = PluginStatus.FAILED
            record.error = f"activation failed: {exc}"
            logger.exception("Plugin %s failed to activate", record.id)

    def unload_all(self) -> None:
        for record in self._registry.list_records():
            if record.status == PluginStatus.ACTIVE:
                self._publish_plugin_event(record, EventType.PLUGIN_UNLOADED)
            self._unregister_event_subscriptions(record)
            if record.instance is not None:
                try:
                    record.instance.on_unload()
                except Exception:  # noqa: BLE001
                    logger.exception("Plugin %s unload failed", record.id)
            record.status = PluginStatus.UNLOADED
            record.instance = None

    def _register_event_subscriptions(self, record: PluginRecord, context: PluginContext) -> None:
        if self._event_bus is None or context.contributions is None:
            return
        for subscription in context.contributions.event_subscriptions:
            sub_id = self._event_bus.subscribe(
                subscription.event_type,
                subscription.handler,
                subscriber_id=f"plugin:{record.id}:{subscription.name}",
                source=f"plugin:{record.id}",
            )
            subscription.subscription_id = sub_id
            record.event_subscription_ids.append(sub_id)

    def _unregister_event_subscriptions(self, record: PluginRecord) -> None:
        if self._event_bus is None:
            return
        for sub_id in list(record.event_subscription_ids):
            self._event_bus.unsubscribe(sub_id)
        record.event_subscription_ids.clear()

    def _publish_plugin_event(self, record: PluginRecord, event_type: str) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            create_event(
                event_type,
                source="plugin-platform",
                payload={
                    "plugin_id": record.id,
                    "plugin_version": record.manifest.version,
                    "status": record.status.value,
                },
            )
        )
