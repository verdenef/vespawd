"""Runtime bootstrap tests."""

from pathlib import Path

from vedaws.project.state import ProjectState
from vedaws.project.init import init_project
from vedaws.project.state.engine import StateEngine
from vedaws.project.state.triggers import TransitionTrigger
from vedaws.runtime.bootstrap import bootstrap
from vedaws.runtime.status import RuntimeStatus
from vedaws.workers.ai_worker import AIExecutableWorker


def test_bootstrap_succeeds_without_project(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    context = bootstrap(tmp_path)
    assert context.status == RuntimeStatus.ACTIVE
    assert context.project is None
    assert context.plugin_count >= 1
    assert context.worker_count >= 1


def test_bootstrap_detects_initialized_project(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path, name="beta")
    context = bootstrap(tmp_path)
    assert context.project is not None
    assert context.project.name == "beta"
    assert context.project.state == ProjectState.CREATED
    assert context.worker_registry.count >= 1
    assert context.dispatcher is not None


def test_bootstrap_wires_ai_service_into_ai_workers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path, name="ai-worker")
    context = bootstrap(tmp_path)
    ai_workers = [
        worker
        for worker in context.worker_registry.list_executable()
        if isinstance(worker, AIExecutableWorker)
    ]
    assert ai_workers
    assert context.ai_service is not None
    assert all(worker.ai_service is context.ai_service for worker in ai_workers)


def test_bootstrap_detection_is_read_only_for_project_manifest(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path, name="readonly-detect")
    engine = StateEngine.load(tmp_path / ".vedaws")
    engine.transition(ProjectState.INITIALIZED, TransitionTrigger.HUMAN_DECISION)

    manifest_path = tmp_path / ".vedaws" / "project.toml"
    original = manifest_path.read_text(encoding="utf-8")
    assert 'state = "created"' in original

    context = bootstrap(tmp_path)
    assert context.project is not None
    assert context.project.state == ProjectState.INITIALIZED

    after = manifest_path.read_text(encoding="utf-8")
    assert after == original
