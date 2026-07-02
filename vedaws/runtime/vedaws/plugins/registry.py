"""Plugin registry with lifecycle records."""

from __future__ import annotations

from dataclasses import dataclass, field

from vedaws.plugins.contributions import PluginContributions
from vedaws.plugins.discovery import PluginDiscoveryResult
from vedaws.plugins.lifecycle import PluginStatus
from vedaws.plugins.manifest import PluginManifest
from vedaws.plugins.sdk import VedawsPlugin


@dataclass
class PluginRecord:
    manifest: PluginManifest
    status: PluginStatus = PluginStatus.DISCOVERED
    source: str = "unknown"
    error: str | None = None
    plugin_class: type[VedawsPlugin] | None = None
    instance: VedawsPlugin | None = None
    contributions: PluginContributions | None = None
    event_subscription_ids: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.manifest.id

    @property
    def is_active(self) -> bool:
        return self.status == PluginStatus.ACTIVE


@dataclass
class PluginRegistry:
    _records: dict[str, PluginRecord] = field(default_factory=dict)
    discovery: PluginDiscoveryResult | None = None
    aggregated_contributions: PluginContributions = field(
        default_factory=PluginContributions
    )

    def register_record(self, record: PluginRecord) -> None:
        self._records[record.id] = record

    def get(self, plugin_id: str) -> PluginRecord | None:
        return self._records.get(plugin_id)

    def list_records(self) -> list[PluginRecord]:
        return sorted(self._records.values(), key=lambda record: record.id)

    def list_active(self) -> list[PluginRecord]:
        return [record for record in self.list_records() if record.is_active]

    def list_plugins(self) -> list[PluginManifest]:
        return [record.manifest for record in self.list_records()]

    @property
    def count(self) -> int:
        return len(self._records)

    @property
    def active_count(self) -> int:
        return len(self.list_active())

    @property
    def invalid_count(self) -> int:
        if self.discovery is None:
            return 0
        return len(self.discovery.invalid)

    @property
    def duplicate_count(self) -> int:
        if self.discovery is None:
            return 0
        return len(self.discovery.duplicates)

    def merge_contributions(self, contributions: PluginContributions) -> None:
        self.aggregated_contributions.merge(contributions)
