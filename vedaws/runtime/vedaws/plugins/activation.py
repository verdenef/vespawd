"""Plugin activation configuration."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from vedaws.config.paths import PROJECT_PLUGINS_FILE, user_config_dir

GLOBAL_PLUGINS_FILE = "plugins.toml"


@dataclass
class PluginActivationConfig:
    enabled: list[str] = field(default_factory=list)
    disabled: list[str] = field(default_factory=list)

    def is_explicitly_enabled(self, plugin_id: str) -> bool:
        return plugin_id in self.enabled

    def is_disabled(self, plugin_id: str) -> bool:
        return plugin_id in self.disabled


def global_plugins_path() -> Path:
    return user_config_dir() / GLOBAL_PLUGINS_FILE


def project_plugins_path(workspace: Path) -> Path | None:
    from vedaws.config.paths import project_config_dir

    config_dir = project_config_dir(workspace)
    if config_dir is None:
        return None
    return config_dir / PROJECT_PLUGINS_FILE


def load_activation_config(path: Path) -> PluginActivationConfig:
    if not path.is_file():
        return PluginActivationConfig()
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    plugins = data.get("plugins", data)
    enabled = [str(item) for item in plugins.get("enabled", []) if str(item).strip()]
    disabled = [str(item) for item in plugins.get("disabled", []) if str(item).strip()]
    return PluginActivationConfig(enabled=enabled, disabled=disabled)


def merge_activation(
    global_config: PluginActivationConfig,
    project_config: PluginActivationConfig | None,
) -> PluginActivationConfig:
    disabled = sorted(set(global_config.disabled) | set(
        project_config.disabled if project_config else []
    ))
    if project_config and project_config.enabled:
        enabled = list(project_config.enabled)
    elif global_config.enabled:
        enabled = list(global_config.enabled)
    else:
        enabled = []
    return PluginActivationConfig(enabled=enabled, disabled=disabled)


def save_activation_config(path: Path, config: PluginActivationConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    enabled_lines = "\n".join(f'  "{plugin_id}",' for plugin_id in config.enabled)
    disabled_lines = "\n".join(f'  "{plugin_id}",' for plugin_id in config.disabled)
    enabled_block = f"[\n{enabled_lines}\n]" if config.enabled else "[]"
    disabled_block = f"[\n{disabled_lines}\n]" if config.disabled else "[]"
    content = (
        "# Vedaws plugin activation\n\n"
        "[plugins]\n"
        f"enabled = {enabled_block}\n"
        f"disabled = {disabled_block}\n"
    )
    path.write_text(content, encoding="utf-8")


def default_project_activation() -> PluginActivationConfig:
    return PluginActivationConfig(enabled=["hello", "git", "mock-ai"], disabled=[])


def enable_plugin(path: Path, plugin_id: str) -> PluginActivationConfig:
    config = load_activation_config(path)
    if plugin_id not in config.enabled:
        config.enabled.append(plugin_id)
    config.disabled = [item for item in config.disabled if item != plugin_id]
    save_activation_config(path, config)
    return config


def disable_plugin(path: Path, plugin_id: str) -> PluginActivationConfig:
    config = load_activation_config(path)
    if plugin_id not in config.disabled:
        config.disabled.append(plugin_id)
    config.enabled = [item for item in config.enabled if item != plugin_id]
    save_activation_config(path, config)
    return config
