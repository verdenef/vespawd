"""Plugin lifecycle states."""

from __future__ import annotations

from enum import Enum


class PluginStatus(str, Enum):
    DISCOVERED = "discovered"
    VALIDATED = "validated"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    UNLOADED = "unloaded"
    DISABLED = "disabled"
    FAILED = "failed"

    def __str__(self) -> str:
        return self.value

    @property
    def is_operational(self) -> bool:
        return self in {
            PluginStatus.VALIDATED,
            PluginStatus.LOADED,
            PluginStatus.INITIALIZED,
            PluginStatus.ACTIVE,
        }
