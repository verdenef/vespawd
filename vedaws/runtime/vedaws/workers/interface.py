"""Worker interface — all workers must implement this contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from vedaws.workers.execution import TaskDispatch, TaskOutcome
from vedaws.workers.models import WorkerHealthReport, WorkerMetadata
from vedaws.workers.status import WorkerStatus


class Worker(ABC):
    """Provider-agnostic worker abstraction."""

    @property
    @abstractmethod
    def metadata(self) -> WorkerMetadata:
        """Return immutable worker metadata."""

    @abstractmethod
    def health_check(self) -> WorkerHealthReport:
        """Return current health without performing task work."""

    @property
    def id(self) -> str:
        return self.metadata.id

    @property
    def status(self) -> WorkerStatus:
        return self.metadata.status

    @property
    def is_executable(self) -> bool:
        return False

    def set_status(self, status: WorkerStatus) -> None:
        """Update lifecycle status."""
        self._set_status(status)

    @abstractmethod
    def _set_status(self, status: WorkerStatus) -> None:
        """Update lifecycle status."""


class ExecutableWorker(Worker):
    """Worker that can execute dispatched tasks."""

    @property
    def is_executable(self) -> bool:
        return True

    @abstractmethod
    def execute(self, dispatch: TaskDispatch) -> TaskOutcome:
        """Perform bounded task work and return an outcome."""
