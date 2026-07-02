"""Plugin manifest and environment validation."""

from __future__ import annotations

from vedaws import __version__
from vedaws.plugins.manifest import PluginManifest
from vedaws.plugins.security import validate_security_declaration
from vedaws.plugins.versioning import python_satisfies, satisfies_constraint


def validate_manifest(manifest: PluginManifest) -> list[str]:
    errors: list[str] = []
    if not manifest.id:
        errors.append("plugin id is required")
    if not manifest.name:
        errors.append("plugin name is required")
    if not manifest.version:
        errors.append("plugin version is required")
    if not manifest.entry_point:
        errors.append("entry_point is required")
    if ":" not in manifest.entry_point:
        errors.append(f"invalid entry_point format: {manifest.entry_point!r}")
    if not satisfies_constraint(__version__, manifest.compatibility.vedaws):
        errors.append(
            f"incompatible vedaws version: requires {manifest.compatibility.vedaws}, "
            f"runtime is {__version__}"
        )
    if not python_satisfies(manifest.compatibility.python):
        errors.append(
            f"incompatible python version: requires {manifest.compatibility.python}"
        )
    errors.extend(validate_security_declaration(manifest.security))
    return errors
