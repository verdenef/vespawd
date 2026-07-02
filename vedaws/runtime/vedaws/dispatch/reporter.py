"""CLI formatting for dispatch and run results."""

from __future__ import annotations

from vedaws.dispatch.models import DispatchResult, DispatchStatus, RunSummary


def format_run_summary(summary: RunSummary) -> str:
    lines = [
        "Run complete:",
        f"  Dispatched: {summary.dispatched}",
        f"  Completed:  {summary.completed}",
        f"  Failed:     {summary.failed}",
        f"  Skipped:    {summary.skipped}",
        f"  Cycles:     {summary.cycles}",
        f"  Retries:    {summary.retries}",
    ]
    if summary.cancelled:
        lines.append("  Status:     cancelled")
    elif summary.blocked:
        lines.append("  Status:     blocked (failure, error, or unresolved readiness)")
    elif summary.dispatched == 0 and summary.skipped > 0:
        lines.append("  Status:     no compatible workers for ready tasks")
    elif summary.dispatched == 0:
        lines.append("  Status:     no ready tasks")
    else:
        lines.append("  Status:     idle")
    if summary.blocking_reason:
        lines.append(f"  Reason:     {summary.blocking_reason}")
    if summary.blocked_tasks:
        lines.append(f"  Blocked:    {', '.join(summary.blocked_tasks[:5])}")

    if summary.results:
        lines.extend(["", "Results:"])
        for result in summary.results:
            lines.append(_format_result_line(result))
    return "\n".join(lines)


def format_dispatch_result(result: DispatchResult) -> str:
    return _format_result_line(result)


def _format_result_line(result: DispatchResult) -> str:
    key = result.task_key or "(none)"
    worker = result.worker_id or "-"
    outcome = ""
    if result.success is True:
        outcome = "success"
    elif result.success is False:
        outcome = "failed"
    detail = f" [{outcome}]" if outcome else ""
    return f"  {key} → {worker} ({result.status.value}){detail}: {result.message}"
