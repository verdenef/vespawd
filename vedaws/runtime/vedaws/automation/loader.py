"""Load automation rules from plugins and project configuration."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

from vedaws.automation.config import AutomationProjectConfig, load_automation_config
from vedaws.automation.model import AutomationRule, RuleAction, RuleCondition

if TYPE_CHECKING:
    from vedaws.plugins.contributions import PluginContributions


def load_project_rules(path: Path) -> list[AutomationRule]:
    if not path.is_file():
        return []
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    rules_data = data.get("rules", [])
    if not isinstance(rules_data, list):
        return []
    rules: list[AutomationRule] = []
    for entry in rules_data:
        if not isinstance(entry, dict):
            continue
        rule = _parse_rule_mapping(entry, source="project")
        if rule is not None:
            rules.append(rule)
    return rules


def load_all_rules(
    workspace: Path,
    *,
    plugin_contributions: PluginContributions | None = None,
    config: AutomationProjectConfig | None = None,
) -> list[AutomationRule]:
    config = config or load_automation_config(workspace)
    merged: dict[str, AutomationRule] = {}

    if plugin_contributions is not None:
        for rule in plugin_contributions.automation_rules:
            merged[rule.id] = rule

    from vedaws.automation.config import automation_config_path

    project_path = automation_config_path(workspace)
    if project_path is not None:
        for rule in load_project_rules(project_path):
            merged[rule.id] = rule

    effective: list[AutomationRule] = []
    for rule in merged.values():
        enabled = rule.enabled
        if rule.id in config.rule_overrides:
            enabled = config.rule_overrides[rule.id]
        effective.append(
            AutomationRule(
                id=rule.id,
                on_event=rule.on_event,
                actions=rule.actions,
                description=rule.description,
                conditions=rule.conditions,
                enabled=enabled and config.enabled,
                source=rule.source,
                plugin_id=rule.plugin_id,
            )
        )
    return sorted(effective, key=lambda item: item.id)


def _parse_rule_mapping(entry: dict, *, source: str) -> AutomationRule | None:
    rule_id = str(entry.get("id", "")).strip()
    on_event = str(entry.get("on_event", "")).strip()
    if not rule_id or not on_event:
        return None
    condition_data = entry.get("if")
    if condition_data is None:
        condition_data = entry.get("conditions")
    conditions = RuleCondition.from_mapping(
        condition_data if isinstance(condition_data, dict) else None
    )
    then_data = entry.get("then")
    actions: list[RuleAction] = []
    if isinstance(then_data, dict):
        actions.append(RuleAction.from_mapping(then_data))
    elif isinstance(then_data, list):
        for action_entry in then_data:
            if isinstance(action_entry, dict):
                actions.append(RuleAction.from_mapping(action_entry))
    enabled = bool(entry.get("enabled", True))
    description = str(entry.get("description", ""))
    return AutomationRule(
        id=rule_id,
        on_event=on_event,
        actions=tuple(actions),
        description=description,
        conditions=conditions,
        enabled=enabled,
        source=source,
    )
