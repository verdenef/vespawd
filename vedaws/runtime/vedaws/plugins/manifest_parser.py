"""Parse vedaws.plugin.toml manifest v1."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from vedaws.plugins.manifest import (
    MANIFEST_VERSION,
    PluginCapabilities,
    PluginCompatibility,
    PluginDependency,
    PluginManifest,
    PluginSecurity,
)

PLUGIN_MANIFEST_FILE = "vedaws.plugin.toml"


def parse_plugin_manifest(path: Path) -> tuple[PluginManifest | None, str | None]:
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except OSError as exc:
        return None, f"cannot read manifest: {exc}"
    except tomllib.TOMLDecodeError as exc:
        return None, f"invalid TOML: {exc}"

    plugin = data.get("plugin", data)
    plugin_id = str(plugin.get("id", "")).strip()
    if not plugin_id:
        return None, "missing plugin id"

    entry_point = str(plugin.get("entry_point", "")).strip()
    if not entry_point:
        return None, "missing entry_point"

    return PluginManifest(
        id=plugin_id,
        name=str(plugin.get("name", plugin_id)),
        version=str(plugin.get("version", "0.0.0")),
        author=str(plugin.get("author", "")),
        description=str(plugin.get("description", "")),
        entry_point=entry_point,
        manifest_version=str(plugin.get("manifest_version", MANIFEST_VERSION)),
        compatibility=_parse_compatibility(plugin, data),
        dependencies=tuple(_parse_dependencies(data.get("dependencies", []))),
        capabilities=_parse_capabilities(data.get("capabilities", {})),
        security=_parse_security(data.get("security", {})),
        path=path.parent,
        manifest_path=path,
    ), None


def _parse_compatibility(plugin: dict[str, Any], data: dict[str, Any]) -> PluginCompatibility:
    compat = plugin.get("compatibility", {})
    if not isinstance(compat, dict):
        compat = data.get("compatibility", {})
    if not isinstance(compat, dict):
        compat = {}
    return PluginCompatibility(
        vedaws=str(compat.get("vedaws", ">=0.1.0")),
        python=str(compat.get("python", ">=3.11")),
    )


def _parse_dependencies(raw: Any) -> list[PluginDependency]:
    if not isinstance(raw, list):
        return []
    deps: list[PluginDependency] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        dep_id = str(entry.get("id", "")).strip()
        if not dep_id:
            continue
        deps.append(
            PluginDependency(
                id=dep_id,
                version=str(entry.get("version", ">=0.0.0")),
            )
        )
    return deps


def _parse_capabilities(raw: Any) -> PluginCapabilities:
    if not isinstance(raw, dict):
        return PluginCapabilities()
    return PluginCapabilities(
        workers=bool(raw.get("workers", False)),
        commands=bool(raw.get("commands", False)),
        workflows=bool(raw.get("workflows", False)),
        projects=bool(raw.get("projects", False)),
        skills=bool(raw.get("skills", False)),
        health_checks=bool(raw.get("health_checks", False)),
        configuration=bool(raw.get("configuration", False)),
    )


def _parse_security(raw: Any) -> PluginSecurity:
    if not isinstance(raw, dict):
        return PluginSecurity()
    permissions = raw.get("permissions", [])
    subprocess_allow = raw.get("subprocess_allow", [])
    if isinstance(permissions, str):
        permissions = [permissions]
    if isinstance(subprocess_allow, str):
        subprocess_allow = [subprocess_allow]
    return PluginSecurity(
        permissions=tuple(str(item).strip() for item in permissions if str(item).strip()),
        subprocess_allow=tuple(
            str(item).strip() for item in subprocess_allow if str(item).strip()
        ),
        network=str(raw.get("network", "none")).strip().lower() or "none",
    )
