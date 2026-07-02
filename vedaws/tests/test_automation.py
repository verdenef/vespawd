"""Automation engine tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from vedaws.cli.app import main
from vedaws.events.bus import EventBus
from vedaws.events.model import create_event
from vedaws.events.types import EventType
from vedaws.project.init import init_project
from vedaws.runtime.bootstrap import bootstrap

from vedaws.automation.conditions import matches_condition
from vedaws.automation.config import load_automation_config
from vedaws.automation.loader import load_project_rules
from vedaws.automation.model import AutomationRule, RuleAction, RuleCondition
from vedaws.automation.registry import AutomationRegistry
from vedaws.automation.validator import validate_rules


def test_condition_matches_task_id() -> None:
    event = create_event(
        EventType.TASK_COMPLETED,
        source="test",
        payload={"task_id": "implement", "workflow_id": "software"},
    )
    condition = RuleCondition.from_mapping({"task": "implement"})
    assert matches_condition(event, condition) is True
    assert matches_condition(event, RuleCondition.from_mapping({"task_id": "review"})) is False


def test_load_project_rules_from_toml(tmp_path: Path) -> None:
    automation_path = tmp_path / ".vedaws" / "automation.toml"
    automation_path.parent.mkdir(parents=True)
    automation_path.write_text(
        """
[[rules]]
id = "project-rule"
description = "Test project rule"
on_event = "TaskCompleted"

[rules.if]
task_id = "plan"

[[rules.then]]
type = "execute_worker"
worker_id = "mock.success"
""",
        encoding="utf-8",
    )
    rules = load_project_rules(automation_path)
    assert len(rules) == 1
    assert rules[0].id == "project-rule"
    assert rules[0].actions[0].params["worker_id"] == "mock.success"


def test_automation_engine_runs_on_event(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path, name="auto-demo")
    context = bootstrap(tmp_path)

    bus = context.event_bus
    assert bus is not None
    engine = context.automation_engine
    assert engine is not None

    registry = AutomationRegistry(
        [
            AutomationRule(
                id="test-worker-on-complete",
                on_event=EventType.TASK_COMPLETED,
                conditions=RuleCondition.from_mapping({"task_id": "plan"}),
                actions=(RuleAction(type="execute_worker", params={"worker_id": "mock.success"}),),
            )
        ]
    )
    from vedaws.automation.engine import AutomationEngine

    test_engine = AutomationEngine(
        registry,
        bus,
        workspace=tmp_path,
        project=context.project,
        dispatcher=context.dispatcher,
        worker_registry=context.worker_registry,
        plugin_registry=context.registry,
    )
    test_engine.attach()

    results = test_engine.run_for_event(
        create_event(
            EventType.TASK_COMPLETED,
            source="test",
            payload={"task_id": "plan"},
        )
    )
    assert len(results) == 1
    assert results[0].success is True


def test_plugin_contributed_software_rule_listed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", "software", "--name", "auto-software"])
    assert main(["automation", "list"]) == 0


def test_automation_enable_disable(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    bootstrap(tmp_path)
    assert main(["automation", "enable", "software.implement-git-status"]) == 0
    config = load_automation_config(tmp_path)
    assert config.rule_overrides["software.implement-git-status"] is True
    assert main(["automation", "disable", "software.implement-git-status"]) == 0
    config = load_automation_config(tmp_path)
    assert config.rule_overrides["software.implement-git-status"] is False


def test_automation_run_rule(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", "software", "--name", "auto-run"])
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    exit_code = main(
        [
            "automation",
            "run",
            "--rule",
            "software.implement-git-status",
            "--event",
            EventType.TASK_COMPLETED,
            "--payload",
            "task_id=implement",
            "--payload",
            "workflow_id=software",
        ]
    )
    assert exit_code == 0


def test_validate_rules_detects_unknown_action() -> None:
    rules = [
        AutomationRule(
            id="bad-rule",
            on_event=EventType.TASK_COMPLETED,
            actions=(RuleAction(type="unknown_action", params={}),),
        )
    ]
    report = validate_rules(rules)
    assert report.error_count == 1


def test_validate_rules_detects_circular_publish() -> None:
    rules = [
        AutomationRule(
            id="rule-a",
            on_event="EventA",
            actions=(RuleAction(type="publish_event", params={"event_type": "EventB"}),),
        ),
        AutomationRule(
            id="rule-b",
            on_event="EventB",
            actions=(RuleAction(type="publish_event", params={"event_type": "EventA"}),),
        ),
    ]
    report = validate_rules(rules)
    assert report.warning_count >= 1


def test_init_creates_automation_toml(tmp_path: Path) -> None:
    init_project(tmp_path, name="automation-init")
    path = tmp_path / ".vedaws" / "automation.toml"
    assert path.is_file()
    assert "automation rules" in path.read_text(encoding="utf-8")


def test_doctor_includes_automation_check(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    assert main(["doctor"]) == 0
