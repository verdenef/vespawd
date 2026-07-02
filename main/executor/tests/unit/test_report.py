"""Executor report builder tests (§10.7)."""

from __future__ import annotations

from vespawd_executor.reporting.report import ExecutorReport, NextAction, build_report


def test_report_includes_required_sections() -> None:
    report = build_report(
        changed=["main/src/a.py"],
        features=["Auth service"],
        run_commands=["uvicorn app:main"],
        test_commands=["pytest"],
        handoff_current=True,
    )
    md = report.to_markdown()
    assert "## What changed" in md
    assert "## How to run and test" in md
    assert "HANDOFF current: yes" in md
    assert "## Next suggested action" in md
    assert "`main/src/a.py`" in md
    assert "Auth service" in md


def test_handoff_ready_signal_and_planner_action() -> None:
    report = build_report(
        changed=["main/src/a.py"],
        handoff_current=True,
        handoff_ready=True,
    )
    md = report.to_markdown()
    assert "Submission handoff is ready for your documenter + rubric." in md
    assert report.next_action is NextAction.PLANNER_FOLLOW_UP


def test_blockers_force_resolve_action() -> None:
    report = build_report(ok=False, blockers=["design_gate_blocked"])
    assert not report.ok
    assert report.next_action is NextAction.RESOLVE_BLOCKERS
    md = report.to_markdown()
    assert "## Blockers" in md
    assert "design_gate_blocked" in md


def test_changes_default_to_human_test() -> None:
    report = build_report(changed=["main/src/a.py"])
    assert report.next_action is NextAction.HUMAN_TEST


def test_no_changes_defaults_to_executor_fix() -> None:
    report = build_report()
    assert report.next_action is NextAction.EXECUTOR_FIX


def test_explicit_next_action_respected() -> None:
    report = build_report(changed=["x"], next_action=NextAction.EXECUTOR_FIX)
    assert report.next_action is NextAction.EXECUTOR_FIX


def test_report_deterministic() -> None:
    kwargs = dict(changed=["a"], features=["f"], handoff_current=True)
    assert build_report(**kwargs).to_markdown() == build_report(**kwargs).to_markdown()


def test_to_dict_roundtrip_fields() -> None:
    report = build_report(changed=["a"], warnings=["w"], handoff_ready=True, handoff_current=True)
    data = report.to_dict()
    assert data["changed"] == ["a"]
    assert data["warnings"] == ["w"]
    assert data["handoff_ready"] is True
    assert data["next_action"] == NextAction.PLANNER_FOLLOW_UP.value


def test_empty_report_placeholders() -> None:
    md = ExecutorReport().to_markdown()
    assert "(no changes recorded)" in md
    assert "(no commands recorded)" in md
