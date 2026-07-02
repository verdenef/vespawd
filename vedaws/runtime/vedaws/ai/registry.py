"""AI provider registry."""

from __future__ import annotations

from collections import defaultdict

from vedaws.ai.provider import AIProvider


class AIProviderRegistry:
    """Runtime-owned registry of contributed AI providers."""

    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}
        self._default_provider_id: str | None = None

    def register(self, provider: AIProvider) -> None:
        self._providers[provider.id] = provider

    def unregister(self, provider_id: str) -> bool:
        if provider_id not in self._providers:
            return False
        del self._providers[provider_id]
        if self._default_provider_id == provider_id:
            self._default_provider_id = None
        return True

    def get(self, provider_id: str) -> AIProvider | None:
        return self._providers.get(provider_id)

    def list_providers(self) -> list[AIProvider]:
        return [self._providers[key] for key in sorted(self._providers)]

    def set_default(self, provider_id: str) -> None:
        if provider_id not in self._providers:
            raise KeyError(f"Unknown AI provider '{provider_id}'")
        self._default_provider_id = provider_id

    @property
    def default_provider_id(self) -> str | None:
        return self._default_provider_id

    def list_capabilities(self) -> dict[str, list[str]]:
        mapping: dict[str, list[str]] = defaultdict(list)
        for provider in self.list_providers():
            for capability in provider.capabilities:
                mapping[capability].append(provider.id)
        for capability in mapping:
            mapping[capability].sort(
                key=lambda provider_id: self._providers[provider_id].priority,
                reverse=True,
            )
        return dict(sorted(mapping.items()))

    @property
    def count(self) -> int:
        return len(self._providers)
