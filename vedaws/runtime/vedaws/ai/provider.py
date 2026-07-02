"""AI provider interface — implemented by provider plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from vedaws.ai.model import (
    ChatRequest,
    ChatResponse,
    EmbeddingsRequest,
    EmbeddingsResponse,
    AIProviderHealth,
    GenerateRequest,
    GenerateResponse,
)


class AIProvider(ABC):
    """Provider-neutral AI interface for plugin implementations."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique provider identifier."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""

    @property
    @abstractmethod
    def capabilities(self) -> tuple[str, ...]:
        """AI capabilities this provider supports."""

    @property
    def priority(self) -> int:
        """Relative selection priority when no config override exists."""
        return 0

    @property
    def plugin_id(self) -> str:
        """Contributing plugin id (set by runtime on registration)."""
        return getattr(self, "_plugin_id", "")

    @plugin_id.setter
    def plugin_id(self, value: str) -> None:
        self._plugin_id = value

    def supports_capability(self, capability: str) -> bool:
        return capability in self.capabilities

    @abstractmethod
    def health(self) -> AIProviderHealth:
        """Report provider and credential availability."""

    @abstractmethod
    def chat(self, request: ChatRequest) -> ChatResponse:
        """Multi-turn conversational completion."""

    @abstractmethod
    def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Single-shot text generation."""

    def stream(self, request: ChatRequest) -> Iterator[str]:
        """Stream chat tokens — optional; default raises NotImplementedError."""
        raise NotImplementedError(f"Provider '{self.id}' does not implement streaming")

    def embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
        """Vector embeddings — optional; default raises NotImplementedError."""
        raise NotImplementedError(f"Provider '{self.id}' does not implement embeddings")

    def metadata(self) -> dict[str, Any]:
        """Optional provider metadata for discovery."""
        return {}
