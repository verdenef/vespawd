"""Plugin discovery and registration."""

from vedaws.plugins.discovery import PluginDiscoveryResult, discover_plugins
from vedaws.plugins.manifest import PluginManifest
from vedaws.plugins.registry import PluginRecord, PluginRegistry
from vedaws.plugins.sdk import PluginContext, VedawsPlugin

__all__ = [
    "PluginContext",
    "PluginDiscoveryResult",
    "PluginManifest",
    "PluginRecord",
    "PluginRegistry",
    "VedawsPlugin",
    "discover_plugins",
]
