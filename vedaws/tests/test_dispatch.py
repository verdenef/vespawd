"""Dispatch and worker execution tests."""

from pathlib import Path

from vedaws.ai.config import AIConfig
from vedaws.ai.model import (
    AIProviderHealth,
    EmbeddingsRequest,
    EmbeddingsResponse,
    GenerateRequest,
    GenerateResponse,
    ChatRequest,
    ChatResponse,
)
from vedaws.ai.provider import AIProvider
from vedaws.ai.registry import AIProviderRegistry
from vedaws.ai.router import AIProviderRouter
from vedaws.ai.service import AIService
from vedaws.dispatch import WorkerDispatcher, run_until_idle
from vedaws.plugins.contributions import PluginSkill
from vedaws.project.init import init_project
from vedaws.project.state import ProjectState, StateEngine, TransitionTrigger
from vedaws.workflow import TaskStatus, WorkflowEngine, WorkflowStatus
from vedaws.workers.ai_worker import AIExecutableWorker
from vedaws.workers.execution import TaskDispatch
from vedaws.workers.mock import register_mock_workers
from vedaws.workers.registry import WorkerRegistry
from vedaws.workflow.models import TaskDefinition


def _setup_project(tmp_path: Path) -> tuple[Path, WorkflowEngine, WorkerDispatcher]:
    init_project(tmp_path)
    config_dir = tmp_path / ".vedaws"
    state_engine = StateEngine.load(config_dir)
    state_engine.transition(ProjectState.INITIALIZED, TransitionTrigger.HUMAN_DECISION)

    workflow = WorkflowEngine.load(config_dir, state_engine=state_engine)
    registry = WorkerRegistry()
    register_mock_workers(registry)
    dispatcher = WorkerDispatcher(workflow, registry, project_name="test")
    workflow.activate("default")
    return config_dir, workflow, dispatcher


def test_capability_matching_selects_success_worker(tmp_path: Path) -> None:
    _, workflow, dispatcher = _setup_project(tmp_path)
    task_def = workflow.task_registry.get_definition("default", "plan")
    assert task_def is not None
    worker = dispatcher.find_worker_for_task(task_def)
    assert worker is not None
    assert worker.id == "mock.success"


def test_dispatch_lifecycle(tmp_path: Path) -> None:
    _, workflow, dispatcher = _setup_project(tmp_path)
    result = dispatcher.dispatch_and_execute("default", "plan")
    assert result.success is True
    assert result.worker_id == "mock.success"

    instance = workflow.task_registry.get_instance("default", "plan")
    assert instance is not None
    assert instance.status == TaskStatus.RECORDED
    assert instance.assigned_worker_id == "mock.success"
    assert instance.outcome_message is not None


def test_run_until_idle_completes_default_workflow(tmp_path: Path) -> None:
    config_dir, workflow, dispatcher = _setup_project(tmp_path)
    summary = run_until_idle(dispatcher)
    assert summary.dispatched == 3
    assert summary.completed == 3
    assert summary.failed == 0
    assert workflow.progress("default").status == WorkflowStatus.COMPLETED

    reloaded = WorkflowEngine.load(config_dir, state_engine=StateEngine.load(config_dir))
    assert reloaded.progress("default").status == WorkflowStatus.COMPLETED


def test_failure_worker_fails_task(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_dir = tmp_path / ".vedaws"
    workflows_dir = config_dir / "workflows"
    workflows_dir.mkdir(exist_ok=True)
    (workflows_dir / "fail.workflow.toml").write_text(
        """
[workflow]
id = "fail"
name = "Failure test"

[[tasks]]
id = "boom"
name = "Boom"
capability = "failure"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    state_engine = StateEngine.load(config_dir)
    state_engine.transition(ProjectState.INITIALIZED, TransitionTrigger.HUMAN_DECISION)
    workflow = WorkflowEngine.load(config_dir, state_engine=state_engine)
    registry = WorkerRegistry()
    register_mock_workers(registry)
    dispatcher = WorkerDispatcher(workflow, registry)

    workflow.activate("fail")
    result = dispatcher.dispatch_and_execute("fail", "boom")
    assert result.success is False
    assert result.worker_id == "mock.failure"

    instance = workflow.task_registry.get_instance("fail", "boom")
    assert instance is not None
    assert instance.status == TaskStatus.FAILED


def test_echo_worker_executes() -> None:
    registry = WorkerRegistry()
    register_mock_workers(registry)
    echo = registry.get("mock.echo")
    assert echo is not None
    outcome = echo.execute(
        TaskDispatch(
            workflow_id="test",
            task_id="echo",
            task=TaskDefinition(id="echo", name="Echo task", capability="echo"),
        )
    )
    assert outcome.status.is_success
    assert "Echo task" in outcome.message


def test_no_worker_for_unknown_capability(tmp_path: Path) -> None:
    _, _, dispatcher = _setup_project(tmp_path)
    worker = dispatcher.find_worker_for_task(
        TaskDefinition(id="x", name="X", capability="nonexistent")
    )
    assert worker is None


def test_ai_capability_alias_routes_provider(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_dir = tmp_path / ".vedaws"
    workflows_dir = config_dir / "workflows"
    (workflows_dir / "ai_alias.workflow.toml").write_text(
        """
[workflow]
id = "ai_alias"
name = "AI Alias"

[[tasks]]
id = "implement"
name = "Implement"
capability = "software-implementation"
ai_capability = "implement"
skills = ["software.testing"]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    state_engine = StateEngine.load(config_dir)
    state_engine.transition(ProjectState.INITIALIZED, TransitionTrigger.HUMAN_DECISION)
    workflow = WorkflowEngine.load(config_dir, state_engine=state_engine)
    registry = WorkerRegistry()

    class AliasAIWorker(AIExecutableWorker):
        def __init__(self) -> None:
            super().__init__(
                worker_id="test.ai.alias",
                name="Alias AI Worker",
                description="AI alias worker",
                capabilities=("software-implementation",),
                provider="test",
            )

    class _TestProvider(AIProvider):
        @property
        def id(self) -> str:
            return "test-ai"

        @property
        def name(self) -> str:
            return "Test AI Provider"

        @property
        def capabilities(self) -> tuple[str, ...]:
            return ("implement",)

        def health(self) -> AIProviderHealth:
            return AIProviderHealth(
                provider_id=self.id, healthy=True, credentials_available=True
            )

        def chat(self, request: ChatRequest) -> ChatResponse:
            return ChatResponse(content=request.messages[-1].content, provider_id=self.id)

        def generate(self, request: GenerateRequest) -> GenerateResponse:
            return GenerateResponse(content=f"ok:{request.prompt}", provider_id=self.id)

        def embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
            return EmbeddingsResponse(vectors=(), provider_id=self.id)

    worker = AliasAIWorker()
    registry.register(worker)
    registry.wire_skills(
        [
            PluginSkill(
                id="software.testing",
                name="Testing",
                description="Verify expected behavior and edge cases",
            )
        ]
    )
    ai_registry = AIProviderRegistry()
    ai_registry.register(_TestProvider())
    ai_service = AIService(ai_registry, AIProviderRouter(ai_registry, AIConfig()))
    registry.wire_ai_service(ai_service)
    dispatcher = WorkerDispatcher(workflow, registry, ai_service=ai_service, workspace=tmp_path)

    workflow.activate("ai_alias")
    result = dispatcher.dispatch_and_execute("ai_alias", "implement")
    assert result.success is True
    assert result.worker_id == "test.ai.alias"
    task_def = workflow.task_registry.get_definition("ai_alias", "implement")
    assert task_def is not None
    outcome = worker.execute(
        TaskDispatch(
            workflow_id="ai_alias",
            task_id="implement",
            task=task_def,
            project_name="test",
            instructions=str(tmp_path),
        )
    )
    assert outcome.status.is_success
    content = str(outcome.data.get("content", ""))
    assert "Skills guidance:" in content
    assert "Testing: Verify expected behavior and edge cases" in content


def test_run_until_idle_blocks_after_retry_when_no_worker_persists(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_dir = tmp_path / ".vedaws"
    workflows_dir = config_dir / "workflows"
    (workflows_dir / "mixed.workflow.toml").write_text(
        """
[workflow]
id = "mixed"
name = "Mixed"

[[tasks]]
id = "ok"
name = "OK"
capability = "success"

[[tasks]]
id = "missing"
name = "Missing worker"
capability = "missing-capability"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    state_engine = StateEngine.load(config_dir)
    state_engine.transition(ProjectState.INITIALIZED, TransitionTrigger.HUMAN_DECISION)
    workflow = WorkflowEngine.load(config_dir, state_engine=state_engine)
    workflow.activate("mixed")

    registry = WorkerRegistry()
    register_mock_workers(registry)
    dispatcher = WorkerDispatcher(workflow, registry)
    summary = run_until_idle(dispatcher)

    assert summary.completed == 1
    assert summary.blocked is True
    assert summary.retries >= 1
    assert summary.blocked_tasks == ["mixed.missing"]


def test_run_until_idle_supports_cancellation(tmp_path: Path) -> None:
    _, _, dispatcher = _setup_project(tmp_path)
    summary = run_until_idle(dispatcher, stop_requested=lambda: True)
    assert summary.cancelled is True
    assert summary.blocked is True
    assert summary.dispatched == 0
