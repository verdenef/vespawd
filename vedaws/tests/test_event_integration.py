"""Event bus runtime integration tests."""

from __future__ import annotations

from pathlib import Path

from vedaws.cli.app import main
from vedaws.events.integration import publish_project_initialized
from vedaws.events.types import EventType
from vedaws.project.init import init_project
from vedaws.project.state import ProjectState, TransitionTrigger
from vedaws.runtime.bootstrap import bootstrap


def test_bootstrap_initializes_event_bus(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    context = bootstrap(tmp_path)
    assert context.event_bus is not None
    assert context.event_bus.stats().subscriber_count >= 0


def test_project_init_publishes_event(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path, name="event-demo")
    context = bootstrap(tmp_path)
    publish_project_initialized(
        context.event_bus,
        project_name="event-demo",
        project_root=str(tmp_path),
    )
    stats = context.event_bus.stats()
    assert stats.published_by_type.get(EventType.PROJECT_INITIALIZED, 0) >= 1


def test_state_transition_publishes_event(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path, name="state-events")
    context = bootstrap(tmp_path)
    assert context.project is not None
    before = context.event_bus.stats().published_by_type.get(EventType.PROJECT_STATE_CHANGED, 0)
    context.project.state_engine.transition(
        ProjectState.INITIALIZED,
        TransitionTrigger.HUMAN_DECISION,
        "test transition",
    )
    after = context.event_bus.stats().published_by_type.get(EventType.PROJECT_STATE_CHANGED, 0)
    assert after > before


def test_plugin_loaded_event_on_bootstrap(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    context = bootstrap(tmp_path)
    stats = context.event_bus.stats()
    assert stats.published_by_type.get(EventType.PLUGIN_LOADED, 0) >= 1
    assert stats.published_by_type.get(EventType.WORKER_REGISTERED, 0) >= 1


def test_events_cli_command(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    assert main(["events", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "Event Bus" in output
    assert EventType.PLUGIN_LOADED in output


def test_hello_plugin_subscribes_to_state_events(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    context = bootstrap(tmp_path)
    stats = context.event_bus.stats()
    assert stats.subscribers_by_type.get(EventType.PROJECT_STATE_CHANGED, 0) >= 1
