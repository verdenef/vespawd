"""Configuration schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vedaws.ai.config import AIConfig


@dataclass
class LoggingConfig:
    level: str | None = None
    file: str | None = None


@dataclass
class PluginsConfig:
    enabled: bool | None = None
    search_paths: list[str] | None = None


@dataclass
class WorkersConfig:
    enabled: bool | None = None
    search_paths: list[str] | None = None


@dataclass
class RuntimeConfig:
    name: str | None = None


@dataclass
class SecurityConfig:
    allow_env_secrets: bool | None = None
    allow_file_secrets: bool | None = None


@dataclass
class ProjectConfigSection:
    name: str = "unnamed"
    state: str = "created"


@dataclass
class VedawsConfig:
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    plugins: PluginsConfig = field(default_factory=PluginsConfig)
    workers: WorkersConfig = field(default_factory=WorkersConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    extensions: dict[str, Any] = field(default_factory=dict)

    def merge(self, other: VedawsConfig) -> VedawsConfig:
        return VedawsConfig(
            logging=_merge_logging(self.logging, other.logging),
            plugins=_merge_plugins(self.plugins, other.plugins),
            workers=_merge_workers(self.workers, other.workers),
            runtime=_merge_runtime(self.runtime, other.runtime),
            ai=_merge_ai(self.ai, other.ai),
            security=_merge_security(self.security, other.security),
            extensions={**self.extensions, **other.extensions},
        )


def _merge_logging(base: LoggingConfig, override: LoggingConfig) -> LoggingConfig:
    return LoggingConfig(
        level=override.level if override.level is not None else base.level,
        file=override.file if override.file is not None else base.file,
    )


def _merge_plugins(base: PluginsConfig, override: PluginsConfig) -> PluginsConfig:
    return PluginsConfig(
        enabled=override.enabled if override.enabled is not None else base.enabled,
        search_paths=override.search_paths if override.search_paths is not None else base.search_paths,
    )


def _merge_workers(base: WorkersConfig, override: WorkersConfig) -> WorkersConfig:
    return WorkersConfig(
        enabled=override.enabled if override.enabled is not None else base.enabled,
        search_paths=override.search_paths if override.search_paths is not None else base.search_paths,
    )


def _merge_runtime(base: RuntimeConfig, override: RuntimeConfig) -> RuntimeConfig:
    return RuntimeConfig(name=override.name if override.name is not None else base.name)


def _merge_ai(base: AIConfig, override: AIConfig) -> AIConfig:
    capabilities = dict(base.capabilities)
    capabilities.update(override.capabilities)
    return AIConfig(
        default_provider=(
            override.default_provider
            if override.default_provider is not None
            else base.default_provider
        ),
        capabilities=capabilities,
    )


def _merge_security(base: SecurityConfig, override: SecurityConfig) -> SecurityConfig:
    return SecurityConfig(
        allow_env_secrets=(
            override.allow_env_secrets
            if override.allow_env_secrets is not None
            else base.allow_env_secrets
        ),
        allow_file_secrets=(
            override.allow_file_secrets
            if override.allow_file_secrets is not None
            else base.allow_file_secrets
        ),
    )
