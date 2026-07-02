"""Automation rule registry."""

from __future__ import annotations

from collections import defaultdict

from vedaws.automation.model import AutomationRule


class AutomationRegistry:
    """In-memory registry of automation rules indexed by event type."""

    def __init__(self, rules: list[AutomationRule] | None = None) -> None:
        self._rules: dict[str, AutomationRule] = {}
        self._by_event: dict[str, list[str]] = defaultdict(list)
        if rules:
            for rule in rules:
                self.register(rule)

    def register(self, rule: AutomationRule) -> None:
        self._rules[rule.id] = rule
        if rule.id not in self._by_event[rule.on_event]:
            self._by_event[rule.on_event].append(rule.id)

    def get(self, rule_id: str) -> AutomationRule | None:
        return self._rules.get(rule_id)

    def list_rules(self) -> list[AutomationRule]:
        return [self._rules[rule_id] for rule_id in sorted(self._rules)]

    def rules_for_event(self, event_type: str) -> list[AutomationRule]:
        return [
            self._rules[rule_id]
            for rule_id in self._by_event.get(event_type, [])
            if rule_id in self._rules
        ]

    @property
    def count(self) -> int:
        return len(self._rules)
