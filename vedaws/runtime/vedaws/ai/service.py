"""AI service facade — runtime entry point for capability requests."""

from __future__ import annotations

from collections.abc import Iterator

from vedaws.ai.model import (
    ChatRequest,
    ChatResponse,
    EmbeddingsRequest,
    EmbeddingsResponse,
    AIProviderHealth,
    GenerateRequest,
    GenerateResponse,
)
from vedaws.ai.provider import AIProvider
from vedaws.ai.registry import AIProviderRegistry
from vedaws.ai.router import AIProviderRouter


class AIService:
    """Request AI capabilities without binding to a specific provider."""

    def __init__(
        self,
        registry: AIProviderRegistry,
        router: AIProviderRouter,
    ) -> None:
        self._registry = registry
        self._router = router

    @property
    def registry(self) -> AIProviderRegistry:
        return self._registry

    @property
    def router(self) -> AIProviderRouter:
        return self._router

    def list_providers(self) -> list[AIProvider]:
        return self._registry.list_providers()

    def list_capabilities(self) -> dict[str, list[str]]:
        return self._registry.list_capabilities()

    def resolve_provider(self, capability: str) -> AIProvider | None:
        return self._router.resolve(capability)

    def resolve_chain(self, capability: str) -> list[AIProvider]:
        return self._router.resolve_chain(capability)

    def provider_health(self, provider_id: str | None = None) -> list[AIProviderHealth]:
        if provider_id is not None:
            provider = self._registry.get(provider_id)
            return [provider.health()] if provider is not None else []
        return [provider.health() for provider in self._registry.list_providers()]

    def chat(self, request: ChatRequest) -> ChatResponse:
        provider = self._require_provider(request.capability)
        response = provider.chat(request)
        if not response.provider_id:
            return ChatResponse(
                content=response.content,
                provider_id=provider.id,
                model=response.model,
                metadata=response.metadata,
            )
        return response

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        provider = self._require_provider(request.capability)
        response = provider.generate(request)
        if not response.provider_id:
            return GenerateResponse(
                content=response.content,
                provider_id=provider.id,
                model=response.model,
                metadata=response.metadata,
            )
        return response

    def stream(self, request: ChatRequest) -> Iterator[str]:
        provider = self._require_provider(request.capability)
        yield from provider.stream(request)

    def embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
        provider = self._require_provider("embeddings")
        response = provider.embeddings(request)
        if not response.provider_id:
            return EmbeddingsResponse(
                vectors=response.vectors,
                provider_id=provider.id,
                model=response.model,
                metadata=response.metadata,
            )
        return response

    def _require_provider(self, capability: str) -> AIProvider:
        provider = self._router.resolve(capability)
        if provider is None:
            raise RuntimeError(
                f"No AI provider available for capability '{capability}'"
            )
        return provider
