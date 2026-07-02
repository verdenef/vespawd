"""AI Provider SDK tests."""

from __future__ import annotations

from pathlib import Path

from vedaws.ai.model import ChatMessage, ChatRequest
from vedaws.ai.registry import AIProviderRegistry
from vedaws.ai.router import AIProviderRouter
from vedaws.ai.config import AIConfig, CapabilityRouting
from vedaws.cli.app import main
from vedaws.config.loader import load_config
from vedaws.project.init import init_project
from vedaws.project.state import ProjectState, TransitionTrigger
from vedaws.runtime.bootstrap import bootstrap


def _mock_provider(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    context = bootstrap(tmp_path)
    service = context.ai_service
    assert service is not None
    provider = service.registry.get("mock-ai")
    assert provider is not None
    return service, provider


def test_mock_provider_chat(tmp_path: Path, monkeypatch) -> None:
    _, provider = _mock_provider(tmp_path, monkeypatch)
    response = provider.chat(
        ChatRequest(
            messages=(ChatMessage(role="user", content="hello"),),
            capability="chat",
        )
    )
    assert "[mock-ai:chat] hello" in response.content


def test_provider_registry_and_unregister(tmp_path: Path, monkeypatch) -> None:
    service, provider = _mock_provider(tmp_path, monkeypatch)
    registry = service.registry
    assert registry.get("mock-ai") is provider
    assert registry.unregister("mock-ai") is True
    assert registry.get("mock-ai") is None


def test_capability_routing_preferred_fallback(tmp_path: Path, monkeypatch) -> None:
    service, _ = _mock_provider(tmp_path, monkeypatch)
    registry = AIProviderRegistry()
    registry.register(service.registry.get("mock-ai"))  # type: ignore[arg-type]
    config = AIConfig(
        default_provider="mock-ai",
        capabilities={
            "implement": CapabilityRouting(preferred="mock-ai", fallback=["mock-ai"]),
        },
    )
    router = AIProviderRouter(registry, config)
    chain = router.resolve_chain("implement")
    assert chain[0].id == "mock-ai"


def test_ai_service_resolves_capability(tmp_path: Path, monkeypatch) -> None:
    service, _ = _mock_provider(tmp_path, monkeypatch)
    response = service.chat(
        ChatRequest(
            messages=(ChatMessage(role="user", content="plan my game"),),
            capability="plan",
        )
    )
    assert response.provider_id == "mock-ai"
    assert "plan my game" in response.content


def test_ai_cli_providers(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    assert main(["ai", "providers"]) == 0
    output = capsys.readouterr().out
    assert "mock-ai" in output


def test_ai_cli_capabilities(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    assert main(["ai", "capabilities"]) == 0
    output = capsys.readouterr().out
    assert "chat" in output


def test_ai_cli_status(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    assert main(["ai", "status"]) == 0


def test_project_ai_config_parsing(tmp_path: Path) -> None:
    init_project(tmp_path)
    config_path = tmp_path / ".vedaws" / "config.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8")
        + """
[ai]
default_provider = "mock-ai"

[ai.capabilities.chat]
preferred = "mock-ai"
fallback = ["mock-ai"]
""",
        encoding="utf-8",
    )
    config = load_config(tmp_path)
    assert config.ai.default_provider == "mock-ai"
    assert config.ai.capabilities["chat"].preferred == "mock-ai"


def test_doctor_includes_ai_platform(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    assert main(["doctor"]) == 0


def test_mock_ai_worker_dispatches_via_ai_service(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    workflows_dir = tmp_path / ".vedaws" / "workflows"
    (workflows_dir / "ai.workflow.toml").write_text(
        """
[workflow]
id = "ai"
name = "AI Workflow"

[[tasks]]
id = "implement"
name = "Implement"
description = "Generate implementation plan"
capability = "implement"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    context = bootstrap(tmp_path)
    assert context.project is not None
    context.project.state_engine.transition(
        ProjectState.INITIALIZED, TransitionTrigger.HUMAN_DECISION
    )
    assert context.dispatcher is not None
    context.project.workflow_engine.activate("ai")
    result = context.dispatcher.dispatch_and_execute("ai", "implement")

    assert result.status.value == "dispatched"
    assert result.success is True
    assert result.worker_id == "mock-ai.executor"
