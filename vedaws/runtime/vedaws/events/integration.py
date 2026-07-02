"""Runtime event wiring helpers."""

from __future__ import annotations

from vedaws.events.bus import EventBus
from vedaws.events.model import create_event
from vedaws.events.types import EventType
from vedaws.project.model import ProjectContext
from vedaws.project.state.engine import StateEngine


def wire_project_events(event_bus: EventBus, project: ProjectContext) -> None:
    """Attach event publishers to project state and workflow engines."""
    _wire_state_engine(event_bus, project.state_engine)
    if project.workflow_engine is not None:
        project.workflow_engine.attach_event_bus(event_bus)


def publish_project_initialized(
    event_bus: EventBus,
    *,
    project_name: str,
    project_root: str,
) -> None:
    event_bus.publish(
        create_event(
            EventType.PROJECT_INITIALIZED,
            source="project-init",
            payload={"project_name": project_name, "project_root": project_root},
        )
    )


def _wire_state_engine(event_bus: EventBus, engine: StateEngine) -> None:
    def on_transition(record) -> None:
        event_bus.publish(
            create_event(
                EventType.PROJECT_STATE_CHANGED,
                source="state-engine",
                payload={
                    "from_state": record.previous_state,
                    "to_state": record.new_state,
                    "trigger": record.trigger,
                    "reason": record.reason or "",
                },
            )
        )

    engine.subscribe(on_transition)
