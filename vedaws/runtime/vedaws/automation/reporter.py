"""Automation listing and execution reporting."""

from __future__ import annotations

from vedaws.automation.model import RuleExecutionResult
from vedaws.automation.registry import AutomationRegistry
from vedaws.automation.validator import AutomationValidationReport


def format_rule_list(registry: AutomationRegistry) -> str:
    lines = ["Automation rules:", ""]
    rules = registry.list_rules()
    if not rules:
        lines.append("  (no rules registered)")
        return "\n".join(lines)

    lines.append(f"  {'ID':<32} {'EVENT':<22} {'ENABLED':<8} SOURCE")
    lines.append(f"  {'-' * 32} {'-' * 22} {'-' * 8} {'-' * 10}")
    for rule in rules:
        enabled = "yes" if rule.enabled else "no"
        source = rule.plugin_id or rule.source
        lines.append(f"  {rule.id:<32} {rule.on_event:<22} {enabled:<8} {source}")
        if rule.description:
            lines.append(f"    {rule.description}")
        if rule.conditions.expressions:
            cond = ", ".join(f"{key}={value}" for key, value in rule.conditions.expressions)
            lines.append(f"    if: {cond}")
        for action in rule.actions:
            lines.append(f"    then: {action.type}")
    return "\n".join(lines)


def format_validation_report(report: AutomationValidationReport) -> str:
    if not report.issues:
        return "Automation validation: no issues"
    lines = ["Automation validation issues:", ""]
    for issue in report.issues:
        lines.append(f"  [{issue.severity}] {issue.rule_id}: {issue.message}")
    return "\n".join(lines)


def format_execution_results(results: list[RuleExecutionResult]) -> str:
    if not results:
        return "No automation rules executed."
    lines = ["Automation execution:", ""]
    for result in results:
        if result.skipped:
            lines.append(
                f"  [skip] {result.rule_id}: {result.skip_reason or 'skipped'}"
            )
            continue
        status = "ok" if result.success else "fail"
        lines.append(f"  [{status}] {result.rule_id} ({result.event_type})")
        for action_result in result.action_results:
            mark = "ok" if action_result.success else "fail"
            lines.append(
                f"    [{mark}] {action_result.action_type}: {action_result.message}"
            )
    return "\n".join(lines)
