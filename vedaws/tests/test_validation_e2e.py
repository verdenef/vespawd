"""End-to-end validation scenarios for real Vedaws usage."""

from __future__ import annotations

from pathlib import Path

from vedaws.ai.model import (
    AIProviderHealth,
    ChatRequest,
    ChatResponse,
    GenerateRequest,
    GenerateResponse,
)
from vedaws.ai.config import AIConfig
from vedaws.ai.provider import AIProvider
from vedaws.ai.registry import AIProviderRegistry
from vedaws.ai.router import AIProviderRouter
from vedaws.ai.service import AIService
from vedaws.cli.app import main
from vedaws.config.loader import load_config
from vedaws.plugins.contributions import PluginSkill
from vedaws.project.detector import detect_project
from vedaws.project.init import init_project
from vedaws.project.state import ProjectState, TransitionTrigger
from vedaws.runtime.bootstrap import bootstrap
from vedaws.workers.ai_worker import AIExecutableWorker
from vedaws.workers.execution import TaskDispatch
from vedaws.workflow.models import TaskDefinition


def test_validation_e2e_software_flow_covers_major_subsystems(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)

    # Project initialization and baseline CLI.
    assert main(["init", "software", "--name", "validation-demo"]) == 0
    assert main(["status", str(tmp_path)]) == 0
    assert "Runtime status" in capsys.readouterr().out

    # Configuration loading.
    config = load_config(tmp_path)
    assert config.runtime.name == "vedaws"
    assert config.plugins.enabled is True

    # Plugin loading, worker registration, AI provider registration.
    context = bootstrap(tmp_path)
    assert context.registry.count >= 1
    assert context.worker_registry.count >= 1
    assert context.worker_registry.get("software.scoping") is not None
    assert context.ai_service is not None
    assert context.ai_service.registry.get("mock-ai") is not None

    # Skills catalog is contributed by plugins.
    skill_count = sum(
        len(record.contributions.skills)
        for record in context.registry.list_records()
        if record.contributions is not None
    )
    assert skill_count >= 1

    # Workflow parsing and readiness.
    assert context.project is not None
    workflow = context.project.workflow_engine.get_workflow("software")
    assert workflow is not None
    assert len(workflow.tasks) >= 1

    # Project detection behavior (read-only path should succeed).
    detected = detect_project(tmp_path, read_only=True)
    assert detected is not None
    assert detected.name == "validation-demo"

    # Artifact-facing commands.
    assert main(["software", "status"]) == 0
    assert "Software artifacts" in capsys.readouterr().out
    assert main(["software", "artifacts"]) == 0

    # Workflow execution, dispatch, and reporting.
    assert main(["state", "transition", "initialized", "--path", str(tmp_path)]) == 0
    assert main(["workflow", "activate", "software", "--path", str(tmp_path)]) == 0
    assert main(["run", "--path", str(tmp_path)]) == 0
    run_output = capsys.readouterr().out
    assert "Run complete:" in run_output

    # Automation rules and plugin command surfaces.
    assert main(["automation", "list", "--path", str(tmp_path)]) == 0
    assert main(["plugins", "list", "--path", str(tmp_path)]) == 0
    assert main(["events", str(tmp_path)]) == 0
    assert main(["ai", "providers"]) == 0
    assert main(["workers", "--path", str(tmp_path)]) == 0

    # Error handling: worker not found and bad workflow id.
    assert main(["workers", "run", "does.not.exist", "--path", str(tmp_path)]) == 1
    assert (
        main(["workflow", "activate", "does-not-exist", "--path", str(tmp_path)]) == 1
    )


def test_validation_e2e_skills_applied_to_ai_worker_prompt(tmp_path: Path) -> None:
    init_project(tmp_path, name="skills-validation")
    config_dir = tmp_path / ".vedaws"
    workflows_dir = config_dir / "workflows"
    workflows_dir.mkdir(exist_ok=True)
    (workflows_dir / "skills_ai.workflow.toml").write_text(
        """
[workflow]
id = "skills_ai"
name = "Skills AI"

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

    class _ValidationAIWorker(AIExecutableWorker):
        def __init__(self) -> None:
            super().__init__(
                worker_id="validation.ai.worker",
                name="Validation AI Worker",
                description="Validation AI worker",
                capabilities=("software-implementation",),
                provider="validation",
            )

    class _ValidationProvider(AIProvider):
        @property
        def id(self) -> str:
            return "validation-provider"

        @property
        def name(self) -> str:
            return "Validation Provider"

        @property
        def capabilities(self) -> tuple[str, ...]:
            return ("implement",)

        def health(self) -> AIProviderHealth:
            return AIProviderHealth(
                provider_id=self.id,
                healthy=True,
                credentials_available=True,
            )

        def generate(self, request: GenerateRequest) -> GenerateResponse:
            return GenerateResponse(content=request.prompt, provider_id=self.id)

        def chat(self, request: ChatRequest) -> ChatResponse:
            content = request.messages[-1].content if request.messages else ""
            return ChatResponse(content=content, provider_id=self.id)

    worker = _ValidationAIWorker()
    worker.bind_skills(
        {
            skill.id: (skill.name, skill.description)
            for skill in (
                PluginSkill(
                    id="software.testing",
                    name="Testing",
                    description="Validate behavior and edge cases",
                ),
            )
        }
    )
    registry = AIProviderRegistry()
    registry.register(_ValidationProvider())
    worker.bind_ai_service(AIService(registry, AIProviderRouter(registry, AIConfig())))

    prompt = worker.build_prompt(
        TaskDispatch(
            workflow_id="skills_ai",
            task_id="implement",
            task=TaskDefinition(
                id="implement",
                name="Implement",
                capability="software-implementation",
                ai_capability="implement",
                skills=("software.testing",),
            ),
            instructions=str(tmp_path),
        )
    )
    assert "Skills guidance:" in prompt
    assert "Testing: Validate behavior and edge cases" in prompt
