"""Unity Game Development plugin tests."""

from __future__ import annotations

from pathlib import Path

from vedaws.cli.app import main
from vedaws.config.loader import load_config
from vedaws.project.init import init_project
from vedaws.project.templates import discover_project_templates, get_project_template
from vedaws.runtime.bootstrap import bootstrap


def test_unity_template_discovered(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = load_config(tmp_path)
    templates = discover_project_templates(config)
    ids = {template.id for template in templates}
    assert "unity" in ids


def test_init_unity_template_layout(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = load_config(tmp_path)
    template = get_project_template(config, "unity")
    assert template is not None
    init_project(tmp_path, name="my-game", template=template)

    assert (tmp_path / "Assets").is_dir()
    assert (tmp_path / "Packages" / "manifest.json").is_file()
    assert (tmp_path / "ProjectSettings" / "ProjectVersion.txt").is_file()
    assert (tmp_path / "Docs" / "game-design" / "GAME_DESIGN.md").is_file()
    assert (tmp_path / ".vedaws" / "workflows" / "unity.workflow.toml").is_file()
    assert not (tmp_path / ".vedaws" / "workflows" / "default.workflow.toml").is_file()

    manifest = (tmp_path / ".vedaws" / "project.toml").read_text(encoding="utf-8")
    assert 'template = "unity"' in manifest


def test_init_unity_cli_shorthand(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["init", "unity", "--name", "cli-unity"]) == 0
    assert (tmp_path / "Docs" / "technical-design" / "TECHNICAL_DESIGN.md").is_file()


def test_unity_workers_registered(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    template = get_project_template(load_config(tmp_path), "unity")
    init_project(tmp_path, template=template)
    context = bootstrap(tmp_path)
    for worker_id in (
        "unity.design",
        "unity.scene",
        "unity.prefab",
        "unity.script",
        "unity.build",
        "unity.test",
        "unity.package",
    ):
        assert context.worker_registry.get(worker_id) is not None


def test_unity_cli_commands(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", "unity", "--name", "unity-demo"])
    assert main(["unity", "status"]) == 0
    output = capsys.readouterr().out
    assert "Unity project layout" in output
    assert main(["unity", "workflow"]) == 0
    assert main(["unity", "build", "--target", "standalone"]) == 0
    assert main(["unity", "package"]) == 0


def test_unity_workflow_has_eight_tasks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", "unity"])
    context = bootstrap(tmp_path)
    assert context.project is not None
    engine = context.project.workflow_engine
    assert engine is not None
    workflow = engine.get_workflow("unity")
    assert workflow is not None
    assert len(workflow.tasks) == 8
