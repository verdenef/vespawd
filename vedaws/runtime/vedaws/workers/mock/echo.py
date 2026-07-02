"""Echo mock worker — returns task name in outcome."""

from __future__ import annotations

from vedaws.workers.execution import TaskDispatch, TaskOutcome
from vedaws.workers.mock.base import MockWorker
from vedaws.workers.mock.metadata import mock_metadata


class EchoWorker(MockWorker):
    def __init__(self) -> None:
        super().__init__(mock_metadata(
            id="mock.echo",
            name="Echo Worker",
            description="Returns the task name as the outcome message",
            capabilities=[("echo", "general")],
        ))

    def execute(self, dispatch: TaskDispatch) -> TaskOutcome:
        return TaskOutcome.success(
            message=f"echo:{dispatch.task.name}",
            task_key=dispatch.key,
        )
