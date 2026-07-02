"""Software workflow workers — capability execution without AI."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from software_plugin.artifacts import ARTIFACT_PATHS, SOFTWARE_WORKFLOW_ID
from vedaws.workers.execution import TaskDispatch, TaskOutcome
from vedaws.workers.interface import ExecutableWorker
from vedaws.workers.models import WorkerCapability, WorkerHealthReport, WorkerMetadata
from vedaws.workers.status import WorkerHealth, WorkerStatus
from vedaws.workers.types import WorkerType

SOFTWARE_CAPABILITIES: tuple[tuple[str, str, str], ...] = (
    ("software-scoping", "Scope & discover", "Clarify goals and constraints"),
    ("software-architecture", "Architecture", "Document system architecture"),
    ("software-api", "API design", "Define interfaces and contracts"),
    ("software-implementation", "Implementation", "Build according to specifications"),
    ("software-testing", "Testing", "Verify behavior and readiness"),
    ("software-review", "Review", "Structured pre-handoff review"),
    ("software-handoff", "Handoff", "Package deliverables for operators"),
)


class SoftwareWorkflowWorker(ExecutableWorker):
    """Executes software lifecycle tasks by updating artifact stubs (no AI)."""

    def __init__(self, capability: str, name: str, description: str) -> None:
        self._capability = capability
        self._metadata = WorkerMetadata(
            id=f"software.{capability.removeprefix('software-')}",
            name=name,
            description=description,
            version="0.1.0",
            worker_type=WorkerType.TOOL,
            capabilities=(WorkerCapability(work_type=capability, scope="software"),),
            status=WorkerStatus.AVAILABLE,
            provider="software-plugin",
            source_path=Path("software_plugin"),
        )

    @property
    def metadata(self) -> WorkerMetadata:
        return self._metadata

    def health_check(self) -> WorkerHealthReport:
        return WorkerHealthReport(
            worker_id=self.id,
            health=WorkerHealth.HEALTHY,
            message="Software workflow worker ready",
        )

    def _set_status(self, status: WorkerStatus) -> None:
        self._metadata = replace(self._metadata, status=status)

    def execute(self, dispatch: TaskDispatch) -> TaskOutcome:
        root = Path(dispatch.instructions).resolve() if dispatch.instructions else Path.cwd()
        message = (
            f"software task completed: {dispatch.key} "
            f"(capability={dispatch.task.capability})"
        )
        self._touch_artifact_for_task(dispatch.task_id, root)
        return TaskOutcome.success(
            message=message,
            task_key=dispatch.key,
            workflow_id=SOFTWARE_WORKFLOW_ID,
            capability=dispatch.task.capability,
        )

    def _touch_artifact_for_task(self, task_id: str, root: Path) -> None:
        mapping = {
            "scope": "docs/architecture/ARCHITECTURE.md",
            "architecture": "docs/architecture/ARCHITECTURE.md",
            "api-design": "docs/api/API.md",
            "implement": "docs/api/API.md",
            "test": "docs/decisions/DECISIONS.md",
            "review": "docs/decisions/DECISIONS.md",
            "handoff": "docs/handoff/HANDOFF.md",
        }
        relative = mapping.get(task_id)
        if relative is None:
            return
        path = root / relative
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            marker = f"\n<!-- completed: {task_id} -->\n"
            if marker.strip() not in text:
                path.write_text(text.rstrip() + marker, encoding="utf-8")


def all_software_workers() -> list[ExecutableWorker]:
    return [
        SoftwareWorkflowWorker(capability, name, description)
        for capability, name, description in SOFTWARE_CAPABILITIES
    ]
