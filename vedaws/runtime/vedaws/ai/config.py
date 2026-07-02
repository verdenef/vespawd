"""AI provider routing configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CapabilityRouting:
    preferred: str | None = None
    fallback: list[str] = field(default_factory=list)


@dataclass
class AIConfig:
    default_provider: str | None = None
    capabilities: dict[str, CapabilityRouting] = field(default_factory=dict)


def parse_ai_config(data: dict[str, Any] | None) -> AIConfig:
    if not data:
        return AIConfig()
    default_provider = data.get("default_provider")
    default_id = str(default_provider).strip() if default_provider else None

    capabilities: dict[str, CapabilityRouting] = {}
    raw_capabilities = data.get("capabilities", {})
    if isinstance(raw_capabilities, dict):
        for capability, routing in raw_capabilities.items():
            if not isinstance(routing, dict):
                continue
            preferred = routing.get("preferred")
            fallback_raw = routing.get("fallback", [])
            fallback: list[str] = []
            if isinstance(fallback_raw, list):
                fallback = [str(item) for item in fallback_raw if str(item).strip()]
            capabilities[str(capability)] = CapabilityRouting(
                preferred=str(preferred) if preferred else None,
                fallback=fallback,
            )
    return AIConfig(default_provider=default_id, capabilities=capabilities)
