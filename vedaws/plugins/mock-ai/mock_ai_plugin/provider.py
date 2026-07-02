"""Mock AI provider — SDK validation, no external APIs."""

from __future__ import annotations

from collections.abc import Iterator

from vedaws.ai.capabilities import STANDARD_AI_CAPABILITIES
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


class MockAIProvider(AIProvider):
    """Deterministic mock provider for platform validation."""

    @property
    def id(self) -> str:
        return "mock-ai"

    @property
    def name(self) -> str:
        return "Mock AI Provider"

    @property
    def capabilities(self) -> tuple[str, ...]:
        return STANDARD_AI_CAPABILITIES + ("embeddings",)

    @property
    def priority(self) -> int:
        return 100

    def health(self) -> AIProviderHealth:
        return AIProviderHealth(
            provider_id=self.id,
            healthy=True,
            credentials_available=True,
            message="Mock provider ready (no credentials required)",
        )

    def chat(self, request: ChatRequest) -> ChatResponse:
        last = request.messages[-1].content if request.messages else ""
        return ChatResponse(
            content=f"[mock-ai:{request.capability}] {last}",
            provider_id=self.id,
            model="mock-model",
        )

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        return GenerateResponse(
            content=f"[mock-ai:{request.capability}] {request.prompt}",
            provider_id=self.id,
            model="mock-model",
        )

    def stream(self, request: ChatRequest) -> Iterator[str]:
        response = self.chat(request)
        yield response.content

    def embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
        vectors = tuple((0.0, 0.0, 0.0) for _ in request.texts)
        return EmbeddingsResponse(
            vectors=vectors,
            provider_id=self.id,
            model="mock-embeddings",
        )
