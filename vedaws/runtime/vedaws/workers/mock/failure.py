"""Failure mock worker — always fails dispatched tasks."""

from __future__ import annotations

from vedaws.workers.execution import TaskDispatch, TaskOutcome
from vedaws.workers.mock.base import MockWorker
from vedaws.workers.mock.metadata import mock_metadata


class FailureWorker(MockWorker):
    def __init__(self) -> None:
        super().__init__(mock_metadata(
            id="mock.failure",
            name="Failure Worker",
            description="Always fails tasks (for testing failure paths)",
            capabilities=[("failure", "general")],
        ))

    def execute(self, dispatch: TaskDispatch) -> TaskOutcome:
        return TaskOutcome.failure(
            message=f"simulated failure for {dispatch.key}",
            task_key=dispatch.key,
        )
