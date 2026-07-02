"""Load plugin entry points."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from vedaws.plugins.manifest import PluginManifest
from vedaws.plugins.sdk import VedawsPlugin


def load_plugin_class(manifest: PluginManifest) -> tuple[type[VedawsPlugin] | None, str | None]:
    if manifest.path is None:
        return None, "plugin path is unknown"

    module_name, _, class_name = manifest.entry_point.partition(":")
    if not module_name or not class_name:
        return None, f"invalid entry_point: {manifest.entry_point}"

    plugin_root = manifest.path
    if str(plugin_root) not in sys.path:
        sys.path.insert(0, str(plugin_root))

    module_path = plugin_root / f"{module_name.replace('.', '/')}.py"
    if not module_path.is_file():
        nested = plugin_root / module_name.replace(".", "/") / "__init__.py"
        if nested.is_file():
            module_path = nested
        else:
            return None, f"module not found for entry_point: {manifest.entry_point}"

    spec = importlib.util.spec_from_file_location(
        f"vedaws_plugin.{manifest.id}.{module_name}",
        module_path,
    )
    if spec is None or spec.loader is None:
        return None, f"cannot load module for {manifest.entry_point}"

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    plugin_cls = getattr(module, class_name, None)
    if plugin_cls is None:
        return None, f"class {class_name!r} not found in {module_name}"
    if not isinstance(plugin_cls, type) or not issubclass(plugin_cls, VedawsPlugin):
        return None, f"{class_name!r} is not a VedawsPlugin subclass"
    return plugin_cls, None
