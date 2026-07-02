"""Plugin manifest v1 model."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class PluginDependency:
    id: str
    version: str = ">=0.0.0"


@dataclass(frozen=True)
class PluginCompatibility:
    vedaws: str = ">=0.1.0"
    python: str = ">=3.11"


@dataclass(frozen=True)
class PluginCapabilities:
    workers: bool = False
    commands: bool = False
    workflows: bool = False
    projects: bool = False
    skills: bool = False
    health_checks: bool = False
    configuration: bool = False


@dataclass(frozen=True)
class PluginSecurity:
    permissions: tuple[str, ...] = ()
    subprocess_allow: tuple[str, ...] = ()
    network: str = "none"


MANIFEST_VERSION = "1"


@dataclass(frozen=True)
class PluginManifest:
    """Canonical plugin manifest v1."""

    id: str
    name: str
    version: str
    entry_point: str
    author: str = ""
    description: str = ""
    manifest_version: str = MANIFEST_VERSION
    compatibility: PluginCompatibility = field(default_factory=PluginCompatibility)
    dependencies: tuple[PluginDependency, ...] = ()
    capabilities: PluginCapabilities = field(default_factory=PluginCapabilities)
    security: PluginSecurity = field(default_factory=PluginSecurity)
    path: Path | None = None
    manifest_path: Path | None = None

    @property
    def display_name(self) -> str:
        return self.name or self.id
