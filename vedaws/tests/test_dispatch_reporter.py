"""Dispatch reporter formatting tests."""

from vedaws.dispatch.models import DispatchResult, DispatchStatus, RunSummary
from vedaws.dispatch.reporter import format_dispatch_result, format_run_summary


def test_format_dispatch_result_includes_key_status_and_message() -> None:
    result = DispatchResult(
        status=DispatchStatus.DISPATCHED,
        workflow_id="wf",
        task_id="task",
        worker_id="worker.a",
        message="done",
        success=True,
    )
    text = format_dispatch_result(result)
    assert "wf.task" in text
    assert "worker.a" in text
    assert "(dispatched)" in text
    assert "[success]" in text
    assert text.endswith(": done")


def test_format_run_summary_reports_blocked_reason_and_task_sample() -> None:
    summary = RunSummary(
        dispatched=1,
        completed=1,
        blocked=True,
        retries=2,
        blocking_reason="No compatible workers",
        blocked_tasks=["wf.a", "wf.b", "wf.c"],
    )
    text = format_run_summary(summary)
    assert "Run complete:" in text
    assert "Status:     blocked" in text
    assert "Reason:     No compatible workers" in text
    assert "Blocked:    wf.a, wf.b, wf.c" in text


def test_format_run_summary_reports_cancelled_state() -> None:
    summary = RunSummary(cancelled=True, blocked=True, blocking_reason="Cancelled by caller")
    text = format_run_summary(summary)
    assert "Status:     cancelled" in text
    assert "Reason:     Cancelled by caller" in text
