"""Task registry — definitions and runtime instances."""

from __future__ import annotations

from dataclasses import dataclass, field

from vedaws.workflow.models import TaskDefinition, TaskInstance, WorkflowDefinition
from vedaws.workflow.states import TaskStatus


@dataclass
class TaskRegistry:
    definitions: dict[str, TaskDefinition] = field(default_factory=dict)
    instances: dict[str, TaskInstance] = field(default_factory=dict)

    def clear(self) -> None:
        self.definitions.clear()
        self.instances.clear()

    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        for task in workflow.tasks:
            key = f"{workflow.id}.{task.id}"
            self.definitions[key] = task

    def get_definition(self, workflow_id: str, task_id: str) -> TaskDefinition | None:
        return self.definitions.get(f"{workflow_id}.{task_id}")

    def get_instance(self, workflow_id: str, task_id: str) -> TaskInstance | None:
        return self.instances.get(f"{workflow_id}.{task_id}")

    def ensure_instance(self, workflow_id: str, task_id: str) -> TaskInstance:
        key = f"{workflow_id}.{task_id}"
        if key not in self.instances:
            self.instances[key] = TaskInstance(workflow_id=workflow_id, task_id=task_id)
        return self.instances[key]

    def list_for_workflow(self, workflow_id: str) -> list[TaskInstance]:
        prefix = f"{workflow_id}."
        return sorted(
            (instance for key, instance in self.instances.items() if key.startswith(prefix)),
            key=lambda instance: instance.task_id,
        )

    def list_all(self) -> list[TaskInstance]:
        return sorted(self.instances.values(), key=lambda instance: instance.key)

    def list_ready(self) -> list[TaskInstance]:
        return [instance for instance in self.list_all() if instance.status == TaskStatus.READY]
