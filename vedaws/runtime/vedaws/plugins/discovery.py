"""Plugin discovery from configured search paths."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from vedaws.config.paths import PLUGIN_MANIFEST_FILE
from vedaws.config.schema import VedawsConfig
from vedaws.plugins.manifest import PluginManifest
from vedaws.plugins.manifest_parser import parse_plugin_manifest

logger = logging.getLogger("vedaws.plugins")


@dataclass
class PluginDiscoveryResult:
    plugins: list[PluginManifest] = field(default_factory=list)
    invalid: list[tuple[Path, str]] = field(default_factory=list)
    duplicates: list[tuple[str, Path, Path]] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.plugins)


def discover_plugins(config: VedawsConfig) -> PluginDiscoveryResult:
    if not config.plugins.enabled:
        logger.info("Plugin discovery disabled by configuration")
        return PluginDiscoveryResult()

    result = PluginDiscoveryResult()
    seen: dict[str, Path] = {}

    for search_path in config.plugins.search_paths:
        root = Path(search_path).expanduser()
        if not root.exists():
            logger.debug("Plugin search path does not exist: %s", root)
            continue
        for manifest_path in _find_manifests(root):
            _register_manifest(manifest_path, seen, result)

    result.plugins.sort(key=lambda plugin: plugin.id)
    logger.info(
        "Discovered %d plugin(s), %d invalid, %d duplicate(s)",
        result.count,
        len(result.invalid),
        len(result.duplicates),
    )
    return result


def _find_manifests(root: Path) -> list[Path]:
    manifests: list[Path] = []
    direct = root / PLUGIN_MANIFEST_FILE
    if direct.is_file():
        manifests.append(direct)
    if not root.is_dir():
        return manifests
    for path in sorted(root.rglob(PLUGIN_MANIFEST_FILE)):
        if path not in manifests:
            manifests.append(path)
    return manifests


def _register_manifest(
    manifest_path: Path,
    seen: dict[str, Path],
    result: PluginDiscoveryResult,
) -> None:
    manifest, error = parse_plugin_manifest(manifest_path)
    if error or manifest is None:
        result.invalid.append((manifest_path, error or "unknown error"))
        logger.warning("Invalid plugin manifest %s: %s", manifest_path, error)
        return
    if manifest.id in seen:
        result.duplicates.append((manifest.id, seen[manifest.id], manifest_path))
        logger.warning("Duplicate plugin id '%s' at %s", manifest.id, manifest_path)
        return
    seen[manifest.id] = manifest_path
    result.plugins.append(manifest)
