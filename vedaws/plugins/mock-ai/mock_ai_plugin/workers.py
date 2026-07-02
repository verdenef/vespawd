"""Mock AI workers used for Milestone 13 integration."""

from __future__ import annotations

from pathlib import Path

from vedaws.ai.capabilities import STANDARD_AI_CAPABILITIES
from vedaws.workers.ai_worker import AIExecutableWorker
from vedaws.workers.interface import ExecutableWorker


class MockAIWorker(AIExecutableWorker):
    """AI worker bound to the mock provider through AIService routing."""

    def __init__(self) -> None:
        super().__init__(
            worker_id="mock-ai.executor",
            name="Mock AI Executor",
            description="Executes standard AI capabilities through AIService",
            capabilities=STANDARD_AI_CAPABILITIES,
            provider="mock-ai-plugin",
            source_path=Path("mock_ai_plugin"),
        )


def all_mock_ai_workers() -> list[ExecutableWorker]:
    return [MockAIWorker()]
