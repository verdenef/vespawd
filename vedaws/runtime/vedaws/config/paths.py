"""Filesystem path resolution for Vedaws configuration and data."""

from __future__ import annotations

import os
from pathlib import Path

USER_CONFIG_DIR_ENV = "VEDAWS_USER_CONFIG_DIR"
PROJECT_CONFIG_DIR_NAME = ".vedaws"
USER_CONFIG_DIR_NAME = ".vedaws"
USER_CONFIG_FILE = "config.toml"
PROJECT_CONFIG_FILE = "config.toml"
PROJECT_MANIFEST_FILE = "project.toml"
PROJECT_STATE_FILE = "state.toml"
PROJECT_HISTORY_FILE = "transitions.jsonl"
PROJECT_WORKFLOWS_DIR = "workflows"
PROJECT_WORKFLOW_PROGRESS_FILE = "workflow-progress.json"
PROJECT_PLUGINS_FILE = "plugins.toml"
PROJECT_AUTOMATION_FILE = "automation.toml"
PLUGIN_MANIFEST_FILE = "vedaws.plugin.toml"


def user_config_dir() -> Path:
    override = os.environ.get(USER_CONFIG_DIR_ENV)
    if override:
        return Path(override).expanduser()
    return Path.home() / USER_CONFIG_DIR_NAME


def user_config_path() -> Path:
    return user_config_dir() / USER_CONFIG_FILE


def project_config_dir(workspace: Path | None = None) -> Path | None:
    root = find_project_root(workspace or Path.cwd())
    if root is None:
        return None
    return root / PROJECT_CONFIG_DIR_NAME


def project_config_path(workspace: Path | None = None) -> Path | None:
    config_dir = project_config_dir(workspace)
    if config_dir is None:
        return None
    return config_dir / PROJECT_CONFIG_FILE


def project_manifest_path(workspace: Path | None = None) -> Path | None:
    config_dir = project_config_dir(workspace)
    if config_dir is None:
        return None
    return config_dir / PROJECT_MANIFEST_FILE


def find_project_root(start: Path) -> Path | None:
    current = start.resolve()
    for directory in (current, *current.parents):
        if (directory / PROJECT_CONFIG_DIR_NAME / PROJECT_MANIFEST_FILE).is_file():
            return directory
    return None


def default_plugin_search_paths(workspace: Path | None = None) -> list[Path]:
    paths: list[Path] = []

    user_plugins = user_config_dir() / "plugins"
    paths.append(user_plugins)

    install_root = package_install_root()
    if install_root is not None:
        paths.append(install_root / "plugins")

    project_root = find_project_root(workspace or Path.cwd())
    if project_root is not None:
        paths.append(project_root / PROJECT_CONFIG_DIR_NAME / "plugins")

    extra = os.environ.get("VEDAWS_PLUGIN_PATHS", "")
    for entry in extra.split(os.pathsep):
        entry = entry.strip()
        if entry:
            paths.append(Path(entry).expanduser())

    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve() if path.exists() else path
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def default_worker_search_paths(workspace: Path | None = None) -> list[Path]:
    paths: list[Path] = []

    user_workers = user_config_dir() / "workers"
    paths.append(user_workers)

    install_root = package_install_root()
    if install_root is not None:
        paths.append(install_root / "workers")

    project_root = find_project_root(workspace or Path.cwd())
    if project_root is not None:
        paths.append(project_root / PROJECT_CONFIG_DIR_NAME / "workers")

    extra = os.environ.get("VEDAWS_WORKER_PATHS", "")
    for entry in extra.split(os.pathsep):
        entry = entry.strip()
        if entry:
            paths.append(Path(entry).expanduser())

    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve() if path.exists() else path
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def package_install_root() -> Path | None:
    """Return the repository or install root that contains bundled plugins."""
    import vedaws

    package_dir = Path(vedaws.__file__).resolve().parent
    runtime_dir = package_dir.parent
    install_root = runtime_dir.parent
    if (install_root / "plugins").is_dir():
        return install_root

    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "plugins").is_dir() and (parent / "runtime").is_dir():
            return parent
    return None
