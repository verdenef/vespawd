"""Unity placeholder workers — Worker SDK, no Unity Editor integration."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from unity_plugin.artifacts import UNITY_WORKFLOW_ID
from vedaws.workers.execution import TaskDispatch, TaskOutcome
from vedaws.workers.interface import ExecutableWorker
from vedaws.workers.models import WorkerCapability, WorkerHealthReport, WorkerMetadata
from vedaws.workers.status import WorkerHealth, WorkerStatus
from vedaws.workers.types import WorkerType

WORKER_DEFINITIONS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    (
        "unity.design",
        "Unity Design Worker",
        "Concept and game design documentation",
        ("unity-concept", "unity-game-design"),
    ),
    (
        "unity.scene",
        "Unity Scene Worker",
        "Scene layout and prototype scaffolding",
        ("unity-prototype", "unity-ui"),
    ),
    (
        "unity.prefab",
        "Unity Prefab Worker",
        "Prefab and gameplay object placeholders",
        ("unity-gameplay",),
    ),
    (
        "unity.script",
        "Unity Script Worker",
        "C# script scaffolding placeholders",
        ("unity-gameplay",),
    ),
    (
        "unity.build",
        "Unity Build Worker",
        "Build configuration placeholders",
        ("unity-build",),
    ),
    (
        "unity.test",
        "Unity Test Worker",
        "Playtest and QA placeholders",
        ("unity-testing",),
    ),
    (
        "unity.package",
        "Unity Package Worker",
        "Package and release placeholders",
        ("unity-release",),
    ),
)

TASK_ARTIFACT_TOUCH: dict[str, str] = {
    "concept": "Docs/game-design/GAME_DESIGN.md",
    "game-design": "Docs/game-design/GAME_DESIGN.md",
    "prototype": "Docs/technical-design/TECHNICAL_DESIGN.md",
    "gameplay": "Docs/technical-design/TECHNICAL_DESIGN.md",
    "ui": "Docs/technical-design/TECHNICAL_DESIGN.md",
    "testing": "Docs/playtests/PLAYTEST_LOG.md",
    "build": "Docs/builds/README.md",
    "release": "Docs/builds/README.md",
}


class UnityWorker(ExecutableWorker):
    """Placeholder Unity worker using the public Worker SDK."""

    def __init__(
        self,
        worker_id: str,
        name: str,
        description: str,
        capabilities: tuple[str, ...],
    ) -> None:
        self._metadata = WorkerMetadata(
            id=worker_id,
            name=name,
            description=description,
            version="0.1.0",
            worker_type=WorkerType.TOOL,
            capabilities=tuple(
                WorkerCapability(work_type=capability, scope="unity")
                for capability in capabilities
            ),
            status=WorkerStatus.AVAILABLE,
            provider="unity-plugin",
            source_path=Path("unity_plugin"),
        )

    @property
    def metadata(self) -> WorkerMetadata:
        return self._metadata

    def health_check(self) -> WorkerHealthReport:
        return WorkerHealthReport(
            worker_id=self.id,
            health=WorkerHealth.HEALTHY,
            message="Unity placeholder worker ready",
        )

    def _set_status(self, status: WorkerStatus) -> None:
        self._metadata = replace(self._metadata, status=status)

    def execute(self, dispatch: TaskDispatch) -> TaskOutcome:
        root = Path(dispatch.instructions).resolve() if dispatch.instructions else Path.cwd()
        self._touch_artifact(dispatch.task_id, root)
        return TaskOutcome.success(
            message=f"unity task completed: {dispatch.key} via {self.id}",
            task_key=dispatch.key,
            workflow_id=UNITY_WORKFLOW_ID,
            capability=dispatch.task.capability,
            worker_id=self.id,
        )

    def _touch_artifact(self, task_id: str, root: Path) -> None:
        relative = TASK_ARTIFACT_TOUCH.get(task_id)
        if relative is None:
            return
        path = root / relative
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            marker = f"\n<!-- completed: {task_id} -->\n"
            if marker.strip() not in text:
                path.write_text(text.rstrip() + marker, encoding="utf-8")


def all_unity_workers() -> list[ExecutableWorker]:
    return [
        UnityWorker(worker_id, name, description, capabilities)
        for worker_id, name, description, capabilities in WORKER_DEFINITIONS
    ]
