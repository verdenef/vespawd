"""Configuration loading with layered overrides."""

from __future__ import annotations

from dataclasses import replace
import os
import tomllib
from pathlib import Path
from typing import Any

from vedaws.ai.config import parse_ai_config
from vedaws.config.defaults import default_config
from vedaws.config.paths import (
    default_plugin_search_paths,
    default_worker_search_paths,
    project_config_path,
    project_manifest_path,
    user_config_path,
)
from vedaws.config.schema import (
    LoggingConfig,
    PluginsConfig,
    ProjectConfigSection,
    RuntimeConfig,
    SecurityConfig,
    VedawsConfig,
    WorkersConfig,
)

SUPPORTED_CONFIGURATION_TYPES = {"string", "boolean", "integer", "number", "array", "object"}


def apply_plugin_configuration(
    config: VedawsConfig,
    plugin_schema: dict[str, Any],
) -> VedawsConfig:
    """Merge and validate plugin-contributed configuration schema against loaded config."""
    if not plugin_schema:
        return config

    merged_extensions = dict(config.extensions)
    for section_name, section_schema in plugin_schema.items():
        _validate_section_schema(section_name, section_schema)

        existing = merged_extensions.get(section_name, {})
        if not isinstance(existing, dict):
            raise ValueError(
                f"Plugin config section '{section_name}' must be a table/object in config"
            )
        merged_section = dict(existing)

        for field_name, field_schema in section_schema.items():
            if field_name not in merged_section and "default" in field_schema:
                merged_section[field_name] = field_schema["default"]
            if field_name in merged_section:
                _validate_field_value(
                    section_name,
                    field_name,
                    merged_section[field_name],
                    str(field_schema["type"]),
                )
        merged_extensions[section_name] = merged_section

    return replace(config, extensions=merged_extensions)


def load_config(workspace: Path | None = None) -> VedawsConfig:
    workspace = workspace or Path.cwd()
    config = default_config()
    config = config.merge(_from_file(user_config_path()))
    project_path = project_config_path(workspace)
    if project_path is not None:
        config = config.merge(_from_file(project_path))
    config = config.merge(_from_environment())
    if not config.plugins.search_paths:
        config.plugins.search_paths = [str(p) for p in default_plugin_search_paths(workspace)]
    if not config.workers.search_paths:
        config.workers.search_paths = [str(p) for p in default_worker_search_paths(workspace)]
    if config.logging.level is None:
        config.logging.level = "INFO"
    if config.plugins.enabled is None:
        config.plugins.enabled = True
    if config.workers.enabled is None:
        config.workers.enabled = True
    if config.runtime.name is None:
        config.runtime.name = "vedaws"
    return config


def load_project_section(workspace: Path | None = None) -> ProjectConfigSection | None:
    manifest = project_manifest_path(workspace)
    if manifest is None or not manifest.is_file():
        return None
    data = _read_toml(manifest)
    project = data.get("project", {})
    return ProjectConfigSection(
        name=str(project.get("name", "unnamed")),
        state=str(project.get("state", "created")),
    )


def _from_file(path: Path) -> VedawsConfig:
    if not path.is_file():
        return VedawsConfig()
    return _from_mapping(_read_toml(path))


def _read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _from_mapping(data: dict[str, Any]) -> VedawsConfig:
    logging_cfg = LoggingConfig()
    plugins_cfg = PluginsConfig()
    workers_cfg = WorkersConfig()
    runtime_cfg = RuntimeConfig()
    security_cfg = SecurityConfig()

    if "logging" in data:
        logging_data = data["logging"]
        logging_cfg = LoggingConfig(
            level=str(logging_data.get("level", "INFO")),
            file=logging_data.get("file"),
        )
    if "plugins" in data:
        plugins_data = data["plugins"]
        plugins_cfg = PluginsConfig(
            enabled=bool(plugins_data.get("enabled", True)),
            search_paths=[str(p) for p in plugins_data.get("search_paths", [])],
        )
    if "workers" in data:
        workers_data = data["workers"]
        workers_cfg = WorkersConfig(
            enabled=bool(workers_data.get("enabled", True)),
            search_paths=[str(p) for p in workers_data.get("search_paths", [])],
        )
    if "runtime" in data:
        runtime_data = data["runtime"]
        runtime_cfg = RuntimeConfig(name=str(runtime_data.get("name", "vedaws")))
    if "security" in data and isinstance(data["security"], dict):
        security_data = data["security"]
        security_cfg = SecurityConfig(
            allow_env_secrets=bool(security_data.get("allow_env_secrets", True)),
            allow_file_secrets=bool(security_data.get("allow_file_secrets", False)),
        )

    ai_cfg = parse_ai_config(data.get("ai") if isinstance(data.get("ai"), dict) else None)

    extensions = {
        key: value
        for key, value in data.items()
        if key
        not in {"logging", "plugins", "workers", "runtime", "project", "ai", "security"}
    }
    return VedawsConfig(
        logging=logging_cfg,
        plugins=plugins_cfg,
        workers=workers_cfg,
        runtime=runtime_cfg,
        ai=ai_cfg,
        security=security_cfg,
        extensions=extensions,
    )


def _from_environment() -> VedawsConfig:
    logging_level = os.environ.get("VEDAWS_LOG_LEVEL")
    logging_file = os.environ.get("VEDAWS_LOG_FILE")
    plugins_enabled = os.environ.get("VEDAWS_PLUGINS_ENABLED")
    plugin_paths = os.environ.get("VEDAWS_PLUGIN_PATHS")
    workers_enabled = os.environ.get("VEDAWS_WORKERS_ENABLED")
    worker_paths = os.environ.get("VEDAWS_WORKER_PATHS")
    runtime_name = os.environ.get("VEDAWS_RUNTIME_NAME")
    allow_env_secrets = os.environ.get("VEDAWS_ALLOW_ENV_SECRETS")
    allow_file_secrets = os.environ.get("VEDAWS_ALLOW_FILE_SECRETS")

    logging_cfg = LoggingConfig()
    if logging_level is not None or logging_file is not None:
        logging_cfg = LoggingConfig(level=logging_level, file=logging_file)

    plugins = PluginsConfig()
    if plugins_enabled is not None:
        plugins.enabled = plugins_enabled.lower() in {"1", "true", "yes", "on"}
    if plugin_paths:
        plugins.search_paths = [p for p in plugin_paths.split(os.pathsep) if p]

    workers = WorkersConfig()
    if workers_enabled is not None:
        workers.enabled = workers_enabled.lower() in {"1", "true", "yes", "on"}
    if worker_paths:
        workers.search_paths = [p for p in worker_paths.split(os.pathsep) if p]

    runtime = RuntimeConfig()
    if runtime_name is not None:
        runtime = RuntimeConfig(name=runtime_name)
    security = SecurityConfig()
    if allow_env_secrets is not None:
        security.allow_env_secrets = allow_env_secrets.lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
    if allow_file_secrets is not None:
        security.allow_file_secrets = allow_file_secrets.lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    return VedawsConfig(
        logging=logging_cfg,
        plugins=plugins,
        workers=workers,
        runtime=runtime,
        security=security,
    )


def _validate_section_schema(section_name: str, section_schema: Any) -> None:
    if not isinstance(section_schema, dict):
        raise ValueError(
            f"Plugin configuration schema section '{section_name}' must be an object"
        )
    for field_name, field_schema in section_schema.items():
        if not isinstance(field_schema, dict):
            raise ValueError(
                f"Plugin configuration field '{section_name}.{field_name}' schema must be an object"
            )
        field_type = field_schema.get("type")
        if field_type not in SUPPORTED_CONFIGURATION_TYPES:
            allowed = ", ".join(sorted(SUPPORTED_CONFIGURATION_TYPES))
            raise ValueError(
                f"Plugin configuration field '{section_name}.{field_name}' has unsupported type '{field_type}' (allowed: {allowed})"
            )


def _validate_field_value(
    section_name: str, field_name: str, value: Any, expected_type: str
) -> None:
    if expected_type == "string" and not isinstance(value, str):
        raise ValueError(f"Expected string for '{section_name}.{field_name}'")
    if expected_type == "boolean" and not isinstance(value, bool):
        raise ValueError(f"Expected boolean for '{section_name}.{field_name}'")
    if expected_type == "integer" and (
        not isinstance(value, int) or isinstance(value, bool)
    ):
        raise ValueError(f"Expected integer for '{section_name}.{field_name}'")
    if expected_type == "number" and (
        (not isinstance(value, int | float)) or isinstance(value, bool)
    ):
        raise ValueError(f"Expected number for '{section_name}.{field_name}'")
    if expected_type == "array" and not isinstance(value, list):
        raise ValueError(f"Expected array for '{section_name}.{field_name}'")
    if expected_type == "object" and not isinstance(value, dict):
        raise ValueError(f"Expected object for '{section_name}.{field_name}'")
