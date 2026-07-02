"""Hello plugin — official Vedaws plugin platform reference."""

from __future__ import annotations

import logging

from vedaws.doctor.model import CheckStatus, HealthCheckResult
from vedaws.events.model import Event
from vedaws.events.types import EventType
from vedaws.plugins.sdk import PluginContext, VedawsPlugin

from hello_plugin.worker import HelloWorker

logger = logging.getLogger("vedaws.plugin.hello")


class HelloPlugin(VedawsPlugin):
    """Reference plugin demonstrating all contribution types."""

    def register(self, context: PluginContext) -> None:
        context.contribute_worker(HelloWorker())
        context.contribute_health_check(self._health_check)
        context.subscribe_event(
            EventType.PROJECT_STATE_CHANGED,
            self._on_project_state_changed,
            name="state-observer",
        )

        if context.plugin_root is not None:
            template = context.plugin_root / "templates" / "hello.workflow.toml"
            if template.is_file():
                context.contribute_workflow_template(template)

        context.contribute_skill(
            "hello.greet",
            "Greet",
            "Demonstrate a plugin-contributed skill",
        )
        context.contribute_command(
            "hello",
            "Say hello from the Hello plugin",
        )
        context.contribute_configuration(
            {
                "hello": {
                    "message": {
                        "type": "string",
                        "default": "Hello, Vedaws!",
                        "description": "Greeting message emitted by the Hello plugin",
                    }
                }
            }
        )

    def _health_check(self) -> HealthCheckResult:
        return HealthCheckResult(
            "hello-plugin",
            CheckStatus.PASS,
            "Hello plugin is active",
        )

    def _on_project_state_changed(self, event: Event) -> None:
        logger.debug(
            "Hello plugin observed %s: %s -> %s",
            event.type,
            event.payload.get("from_state"),
            event.payload.get("to_state"),
        )
