"""Project context model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from typing import TYPE_CHECKING

from vedaws.project.state.engine import StateEngine
from vedaws.project.state.states import ProjectState

if TYPE_CHECKING:
    from vedaws.workflow.engine import WorkflowEngine


@dataclass
class ProjectContext:
    root: Path
    name: str
    state_engine: StateEngine
    workflow_engine: WorkflowEngine | None = None

    @property
    def state(self) -> ProjectState:
        return self.state_engine.current

    @property
    def state_name(self) -> str:
        return self.state_engine.current.value

    @classmethod
    def placeholder(cls) -> ProjectContext:
        raise RuntimeError("No project context available")
