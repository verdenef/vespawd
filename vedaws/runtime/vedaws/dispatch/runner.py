"""Orchestration runner — execute all READY tasks until idle."""

from __future__ import annotations

import logging
from collections.abc import Callable

from vedaws.dispatch.dispatcher import WorkerDispatcher
from vedaws.dispatch.models import DispatchStatus, RunSummary

logger = logging.getLogger("vedaws.dispatch")


def run_until_idle(
    dispatcher: WorkerDispatcher,
    *,
    max_tasks: int | None = None,
    max_cycles: int = 1000,
    stop_requested: Callable[[], bool] | None = None,
) -> RunSummary:
    """Dispatch and execute READY tasks until idle, blocked, or cancelled."""
    summary = RunSummary()
    limit = max_tasks if max_tasks is not None else 10_000
    cycles = 0

    while summary.dispatched < limit and cycles < max_cycles:
        if stop_requested is not None and stop_requested():
            summary.cancelled = True
            summary.blocked = True
            summary.blocking_reason = "Run cancelled by caller"
            break
        cycles += 1
        summary.cycles = cycles
        ready = dispatcher.list_ready_tasks()
        if not ready:
            break

        progressed_this_cycle = False
        unresolved_no_worker: list[str] = []
        for task in sorted(ready, key=lambda item: (item.workflow_id, item.task_id)):
            if summary.dispatched >= limit:
                break
            result = dispatcher.dispatch_and_execute(task.workflow_id, task.task_id)
            summary.results.append(result)
            task_key = f"{task.workflow_id}.{task.task_id}"

            if result.status == DispatchStatus.DISPATCHED:
                summary.dispatched += 1
                progressed_this_cycle = True
                if result.success:
                    summary.completed += 1
                else:
                    summary.failed += 1
                    summary.blocked = True
                    summary.blocking_reason = (
                        f"Task {task_key} failed during dispatch execution"
                    )
                    summary.blocked_tasks = [task_key]
                    break
            elif result.status == DispatchStatus.NO_WORKER:
                summary.skipped += 1
                unresolved_no_worker.append(task_key)
            else:
                summary.skipped += 1
                if result.status == DispatchStatus.ERROR:
                    summary.failed += 1
                    summary.blocked = True
                    summary.blocking_reason = (
                        f"Task {task_key} produced dispatch error: {result.message}"
                    )
                    summary.blocked_tasks = [task_key]
                    break

        if summary.blocked:
            break

        if unresolved_no_worker:
            summary.retries += len(unresolved_no_worker)
            if not progressed_this_cycle:
                summary.failed += 1
                summary.blocked = True
                summary.blocked_tasks = unresolved_no_worker
                sample = ", ".join(unresolved_no_worker[:5])
                summary.blocking_reason = (
                    "No compatible workers for ready tasks after deterministic retry pass: "
                    f"{sample}"
                )
                logger.warning("%s", summary.blocking_reason)
                break

    if cycles >= max_cycles and not summary.blocked:
        summary.blocked = True
        summary.blocking_reason = f"Run loop reached max_cycles={max_cycles}"

    return summary
