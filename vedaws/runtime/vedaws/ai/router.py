"""Capability-based AI provider selection."""

from __future__ import annotations

import logging

from vedaws.ai.config import AIConfig
from vedaws.ai.provider import AIProvider
from vedaws.ai.registry import AIProviderRegistry

logger = logging.getLogger("vedaws.ai")


class AIProviderRouter:
    """Resolve providers from project config, capability, and registry priorities."""

    def __init__(self, registry: AIProviderRegistry, config: AIConfig) -> None:
        self._registry = registry
        self._config = config
        if config.default_provider:
            try:
                self._registry.set_default(config.default_provider)
            except KeyError:
                logger.debug(
                    "Configured default provider '%s' is not registered",
                    config.default_provider,
                )

    @property
    def config(self) -> AIConfig:
        return self._config

    def resolve(self, capability: str) -> AIProvider | None:
        candidates = self.resolve_chain(capability)
        return candidates[0] if candidates else None

    def resolve_chain(self, capability: str) -> list[AIProvider]:
        ordered_ids: list[str] = []
        routing = self._config.capabilities.get(capability)
        if routing is not None:
            if routing.preferred:
                ordered_ids.append(routing.preferred)
            ordered_ids.extend(routing.fallback)

        if self._registry.default_provider_id:
            ordered_ids.append(self._registry.default_provider_id)

        for provider in sorted(
            self._registry.list_providers(),
            key=lambda item: item.priority,
            reverse=True,
        ):
            if provider.supports_capability(capability):
                ordered_ids.append(provider.id)

        seen: set[str] = set()
        providers: list[AIProvider] = []
        for provider_id in ordered_ids:
            if provider_id in seen:
                continue
            seen.add(provider_id)
            provider = self._registry.get(provider_id)
            if provider is None:
                continue
            if not provider.supports_capability(capability):
                continue
            providers.append(provider)
        return providers
