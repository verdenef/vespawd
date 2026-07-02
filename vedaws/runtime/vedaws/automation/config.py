"""Project automation configuration — enable/disable rules."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from vedaws.config.paths import PROJECT_AUTOMATION_FILE, project_config_dir


@dataclass
class AutomationProjectConfig:
    enabled: bool = True
    rule_overrides: dict[str, bool] = field(default_factory=dict)


def automation_config_path(workspace: Path) -> Path | None:
    config_dir = project_config_dir(workspace)
    if config_dir is None:
        return None
    return config_dir / PROJECT_AUTOMATION_FILE


def load_automation_config(workspace: Path) -> AutomationProjectConfig:
    path = automation_config_path(workspace)
    if path is None or not path.is_file():
        return AutomationProjectConfig()
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    automation = data.get("automation", {})
    enabled = bool(automation.get("enabled", True))
    overrides: dict[str, bool] = {}
    raw_overrides = automation.get("overrides", {})
    if isinstance(raw_overrides, dict):
        for rule_id, override in raw_overrides.items():
            if isinstance(override, dict) and "enabled" in override:
                overrides[str(rule_id)] = bool(override["enabled"])
    rules_section = automation.get("rules", {})
    if isinstance(rules_section, dict):
        for rule_id, override in rules_section.items():
            if isinstance(override, dict) and "enabled" in override:
                overrides[str(rule_id)] = bool(override["enabled"])
    return AutomationProjectConfig(enabled=enabled, rule_overrides=overrides)


def save_rule_override(workspace: Path, rule_id: str, *, enabled: bool) -> Path:
    path = automation_config_path(workspace)
    if path is None:
        raise FileNotFoundError("No Vedaws project found")
    config = load_automation_config(workspace)
    config.rule_overrides[rule_id] = enabled
    _write_automation_config(path, config)
    return path


def _write_automation_config(path: Path, config: AutomationProjectConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Vedaws automation configuration",
        "",
        "[automation]",
        f"enabled = {'true' if config.enabled else 'false'}",
        "",
    ]
    if config.rule_overrides:
        lines.append("[automation.overrides]")
        for rule_id in sorted(config.rule_overrides):
            flag = "true" if config.rule_overrides[rule_id] else "false"
            lines.append(f'"{rule_id}".enabled = {flag}')
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
