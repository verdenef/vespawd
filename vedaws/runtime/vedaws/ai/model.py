"""AI request/response models — provider-neutral."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class ChatRequest:
    messages: tuple[ChatMessage, ...]
    capability: str = "chat"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChatResponse:
    content: str
    provider_id: str = ""
    model: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerateRequest:
    prompt: str
    capability: str = "chat"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerateResponse:
    content: str
    provider_id: str = ""
    model: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddingsRequest:
    texts: tuple[str, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddingsResponse:
    vectors: tuple[tuple[float, ...], ...]
    provider_id: str = ""
    model: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AIProviderHealth:
    provider_id: str
    healthy: bool
    credentials_available: bool
    message: str = ""
