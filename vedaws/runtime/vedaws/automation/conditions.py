"""Condition evaluation against event payloads."""

from __future__ import annotations

from vedaws.automation.model import RuleCondition
from vedaws.events.model import Event


def matches_condition(event: Event, condition: RuleCondition) -> bool:
    if not condition.expressions:
        return True
    payload = dict(event.payload)
    for key, expected in condition.expressions:
        actual = payload.get(key)
        if actual is None:
            return False
        if str(actual) != expected:
            return False
    return True
