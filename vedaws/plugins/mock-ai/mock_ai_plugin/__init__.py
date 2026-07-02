"""Mock AI provider plugin."""

from __future__ import annotations

from mock_ai_plugin.provider import MockAIProvider
from mock_ai_plugin.workers import all_mock_ai_workers
from vedaws.doctor.model import CheckStatus, HealthCheckResult
from vedaws.plugins.sdk import PluginContext, VedawsPlugin


class MockAIPlugin(VedawsPlugin):
    """Reference AI provider plugin for the Vedaws AI Provider SDK."""

    def register(self, context: PluginContext) -> None:
        context.contribute_ai_provider(MockAIProvider())
        for worker in all_mock_ai_workers():
            context.contribute_worker(worker)
        context.contribute_health_check(self._health_check)

    def _health_check(self) -> HealthCheckResult:
        provider = MockAIProvider()
        health = provider.health()
        return HealthCheckResult(
            "mock-ai provider",
            CheckStatus.PASS if health.healthy else CheckStatus.FAIL,
            health.message,
        )
