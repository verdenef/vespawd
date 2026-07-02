"""Build AI platform from plugin contributions."""

from __future__ import annotations

from vedaws.ai.config import AIConfig, parse_ai_config
from vedaws.ai.provider import AIProvider
from vedaws.ai.registry import AIProviderRegistry
from vedaws.ai.router import AIProviderRouter
from vedaws.ai.service import AIService
from vedaws.config.schema import VedawsConfig
from vedaws.plugins.registry import PluginRegistry


def build_ai_service(
    registry: PluginRegistry,
    config: VedawsConfig,
) -> AIService:
    ai_registry = AIProviderRegistry()
    for record in registry.list_active():
        if record.contributions is None:
            continue
        for provider in record.contributions.ai_providers:
            _register_provider(ai_registry, provider, record.id)

    ai_config = _ai_config_from_vedaws_config(config)
    router = AIProviderRouter(ai_registry, ai_config)
    return AIService(ai_registry, router)


def _register_provider(
    ai_registry: AIProviderRegistry,
    provider: AIProvider,
    plugin_id: str,
) -> None:
    provider.plugin_id = plugin_id
    ai_registry.register(provider)


def _ai_config_from_vedaws_config(config: VedawsConfig) -> AIConfig:
    if config.ai.default_provider or config.ai.capabilities:
        return config.ai
    raw = config.extensions.get("ai")
    if isinstance(raw, dict):
        return parse_ai_config(raw)
    return AIConfig()
