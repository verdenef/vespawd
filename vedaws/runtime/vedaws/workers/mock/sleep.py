"""Sleep mock worker — simulates delayed execution."""

from __future__ import annotations

import time

from vedaws.workers.execution import TaskDispatch, TaskOutcome
from vedaws.workers.mock.base import MockWorker
from vedaws.workers.mock.metadata import mock_metadata


class SleepWorker(MockWorker):
    def __init__(self, delay_seconds: float = 0.05) -> None:
        super().__init__(mock_metadata(
            id="mock.sleep",
            name="Sleep Worker",
            description="Simulates work by sleeping briefly",
            capabilities=[("sleep", "general")],
        ))
        self._delay = delay_seconds

    def execute(self, dispatch: TaskDispatch) -> TaskOutcome:
        time.sleep(self._delay)
        return TaskOutcome.success(
            message=f"slept:{self._delay}s",
            task_key=dispatch.key,
        )
