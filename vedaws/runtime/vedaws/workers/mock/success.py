"""Success mock worker — completes tasks for common workflow capabilities."""

from __future__ import annotations

from vedaws.workers.execution import TaskDispatch, TaskOutcome
from vedaws.workers.mock.base import MockWorker
from vedaws.workers.mock.metadata import mock_metadata

DEFAULT_SUCCESS_CAPABILITIES = [
    ("planning", "general"),
    ("validation", "general"),
    ("review", "general"),
    ("success", "general"),
]


class SuccessWorker(MockWorker):
    def __init__(self) -> None:
        super().__init__(mock_metadata(
            id="mock.success",
            name="Success Worker",
            description="Always completes tasks successfully",
            capabilities=DEFAULT_SUCCESS_CAPABILITIES,
        ))

    def execute(self, dispatch: TaskDispatch) -> TaskOutcome:
        return TaskOutcome.success(
            message=f"completed:{dispatch.key}",
            task_key=dispatch.key,
            capability=dispatch.task.capability,
        )
