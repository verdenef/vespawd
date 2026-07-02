"""Automation rule data model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


ACTION_EXECUTE_WORKER = "execute_worker"
ACTION_PUBLISH_EVENT = "publish_event"
ACTION_TRANSITION_STATE = "transition_state"
ACTION_WORKFLOW_STEP = "workflow_step"
ACTION_PLUGIN_COMMAND = "plugin_command"

KNOWN_ACTION_TYPES: frozenset[str] = frozenset({
    ACTION_EXECUTE_WORKER,
    ACTION_PUBLISH_EVENT,
    ACTION_TRANSITION_STATE,
    ACTION_WORKFLOW_STEP,
    ACTION_PLUGIN_COMMAND,
})

CONDITION_ALIASES: dict[str, str] = {
    "task": "task_id",
    "workflow": "workflow_id",
    "worker": "worker_id",
    "plugin": "plugin_id",
    "state": "state",
}


@dataclass(frozen=True)
class RuleCondition:
    """Key/value conditions matched against event payload (all must match)."""

    expressions: tuple[tuple[str, str], ...] = ()

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None) -> RuleCondition:
        if not data:
            return cls()
        pairs: list[tuple[str, str]] = []
        for key, value in data.items():
            if value is None:
                continue
            normalized_key = CONDITION_ALIASES.get(key, key)
            pairs.append((normalized_key, str(value)))
        return cls(expressions=tuple(pairs))


@dataclass(frozen=True)
class RuleAction:
    """Single automation action."""

    type: str
    params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> RuleAction:
        action_type = str(data.get("type") or data.get("action") or "").strip()
        params = {
            key: value
            for key, value in data.items()
            if key not in {"type", "action"}
        }
        return cls(type=action_type, params=params)


@dataclass(frozen=True)
class AutomationRule:
    """Event → condition → action(s) rule definition."""

    id: str
    on_event: str
    actions: tuple[RuleAction, ...]
    description: str = ""
    conditions: RuleCondition = field(default_factory=RuleCondition)
    enabled: bool = True
    source: str = "project"
    plugin_id: str = ""

    @property
    def is_plugin_rule(self) -> bool:
        return bool(self.plugin_id)


@dataclass
class RuleActionResult:
    rule_id: str
    action_type: str
    success: bool
    message: str = ""


@dataclass
class RuleExecutionResult:
    rule_id: str
    event_type: str
    matched: bool
    skipped: bool = False
    skip_reason: str = ""
    action_results: list[RuleActionResult] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return not self.skipped and all(result.success for result in self.action_results)
