"""Generic project template discovery and application."""

from __future__ import annotations

import logging
import shutil
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from vedaws.config.schema import VedawsConfig
from vedaws.plugins.discovery import discover_plugins

logger = logging.getLogger("vedaws.project")

TEMPLATE_MANIFEST = "template.toml"
PROJECT_TEMPLATE_DIR = Path("templates") / "project"


@dataclass(frozen=True)
class ProjectTemplate:
    id: str
    name: str
    description: str
    root: Path
    version: str = "0.1.0"
    default_workflow: str | None = None
    skip_default_workflow: bool = False
    scaffold_dir: str | None = None
    plugin_id: str = ""
    plugins_enabled: tuple[str, ...] = ()


@dataclass
class ProjectTemplateApplyResult:
    template_id: str
    workflows_installed: list[str] = field(default_factory=list)
    scaffold_paths: list[str] = field(default_factory=list)


def discover_project_templates(config: VedawsConfig) -> list[ProjectTemplate]:
    """Discover project templates from plugin packages without requiring activation."""
    templates: list[ProjectTemplate] = []
    seen: set[str] = set()
    if not config.plugins.enabled:
        return templates

    for manifest in discover_plugins(config).plugins:
        if manifest.path is None:
            continue
        template_root = manifest.path / PROJECT_TEMPLATE_DIR
        parsed = parse_project_template(template_root, plugin_id=manifest.id)
        if parsed is None or parsed.id in seen:
            continue
        seen.add(parsed.id)
        templates.append(parsed)

    return sorted(templates, key=lambda template: template.id)


def get_project_template(config: VedawsConfig, template_id: str) -> ProjectTemplate | None:
    for template in discover_project_templates(config):
        if template.id == template_id:
            return template
    return None


def parse_project_template(
    template_root: Path,
    *,
    plugin_id: str = "",
) -> ProjectTemplate | None:
    manifest_path = template_root / TEMPLATE_MANIFEST
    if not manifest_path.is_file():
        return None
    with manifest_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("template", data)
    template_id = str(section.get("id", "")).strip()
    if not template_id:
        return None
    plugins_section = data.get("plugins", {})
    enabled = tuple(
        str(item).strip()
        for item in plugins_section.get("enabled", [])
        if str(item).strip()
    )
    return ProjectTemplate(
        id=template_id,
        name=str(section.get("name", template_id)),
        description=str(section.get("description", "")),
        root=template_root,
        version=str(section.get("version", "0.1.0")),
        default_workflow=str(section.get("default_workflow", "")).strip() or None,
        skip_default_workflow=bool(section.get("skip_default_workflow", False)),
        scaffold_dir=str(section.get("scaffold_dir", "scaffold")).strip() or None,
        plugin_id=plugin_id,
        plugins_enabled=enabled,
    )


def apply_project_template(
    template: ProjectTemplate,
    workspace: Path,
    config_dir: Path,
) -> ProjectTemplateApplyResult:
    """Apply a discovered plugin project template to an initialized project."""
    result = ProjectTemplateApplyResult(template_id=template.id)
    workspace = workspace.resolve()

    if template.skip_default_workflow:
        default_workflow = config_dir / "workflows" / "default.workflow.toml"
        if default_workflow.is_file():
            default_workflow.unlink()

    workflows_src = template.root / "workflows"
    if workflows_src.is_dir():
        workflows_dst = config_dir / "workflows"
        workflows_dst.mkdir(parents=True, exist_ok=True)
        for workflow_file in sorted(workflows_src.glob("*.workflow.toml")):
            target = workflows_dst / workflow_file.name
            shutil.copy2(workflow_file, target)
            result.workflows_installed.append(
                workflow_file.name.removesuffix(".workflow.toml")
            )

    if template.scaffold_dir:
        scaffold_root = template.root / template.scaffold_dir
        if scaffold_root.is_dir():
            for source in sorted(scaffold_root.rglob("*")):
                if source.is_dir():
                    continue
                relative = source.relative_to(scaffold_root)
                target = workspace / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                result.scaffold_paths.append(str(relative).replace("\\", "/"))

    _write_template_manifest(workspace, config_dir, template)
    if template.plugins_enabled:
        from vedaws.plugins.activation import load_activation_config, save_activation_config

        plugins_path = config_dir / "plugins.toml"
        activation = load_activation_config(plugins_path)
        merged = sorted(set(activation.enabled) | set(template.plugins_enabled))
        activation.enabled = merged
        save_activation_config(plugins_path, activation)

    logger.info(
        "Applied project template '%s' — %d workflow(s), %d scaffold file(s)",
        template.id,
        len(result.workflows_installed),
        len(result.scaffold_paths),
    )
    return result


def _write_template_manifest(
    workspace: Path,
    config_dir: Path,
    template: ProjectTemplate,
) -> None:
    from vedaws.config.paths import PROJECT_MANIFEST_FILE

    manifest_path = config_dir / PROJECT_MANIFEST_FILE
    if not manifest_path.is_file():
        return
    text = manifest_path.read_text(encoding="utf-8")
    if f'template = "{template.id}"' in text:
        return
    lines = text.splitlines()
    inserted = False
    for index, line in enumerate(lines):
        if line.strip() == "[project]":
            lines.insert(index + 1, f'template = "{template.id}"')
            inserted = True
            break
    if inserted:
        manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
