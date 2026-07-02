"""Software Workflow plugin tests."""

from __future__ import annotations

from pathlib import Path

from vedaws.cli.app import main
from vedaws.project.templates import discover_project_templates, get_project_template
from vedaws.config.loader import load_config
from vedaws.project.init import init_project
from vedaws.runtime.bootstrap import bootstrap


def test_software_template_discovered(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = load_config(tmp_path)
    templates = discover_project_templates(config)
    ids = {template.id for template in templates}
    assert "software" in ids


def test_init_software_template(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = load_config(tmp_path)
    template = get_project_template(config, "software")
    assert template is not None
    init_project(tmp_path, name="demo-app", template=template)

    assert (tmp_path / "docs" / "architecture" / "ARCHITECTURE.md").is_file()
    assert (tmp_path / ".vedaws" / "workflows" / "software.workflow.toml").is_file()
    assert not (tmp_path / ".vedaws" / "workflows" / "default.workflow.toml").is_file()

    manifest = (tmp_path / ".vedaws" / "project.toml").read_text(encoding="utf-8")
    assert 'template = "software"' in manifest


def test_init_software_cli_shorthand(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["init", "software", "--name", "cli-software"]) == 0
    assert (tmp_path / "docs" / "api" / "API.md").is_file()


def test_software_workers_registered(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = load_config(tmp_path)
    template = get_project_template(config, "software")
    init_project(tmp_path, template=template)
    context = bootstrap(tmp_path)
    assert context.worker_registry.get("software.scoping") is not None
    assert context.worker_registry.get("software.handoff") is not None


def test_software_cli_status_and_artifacts(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", "--template", "software", "--name", "status-demo"])
    assert main(["software", "status"]) == 0
    output = capsys.readouterr().out
    assert "Software artifacts" in output
    assert main(["software", "artifacts"]) == 0


def test_software_workflow_loaded(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", "software"])
    context = bootstrap(tmp_path)
    assert context.project is not None
    engine = context.project.workflow_engine
    assert engine is not None
    workflow = engine.get_workflow("software")
    assert workflow is not None
    assert len(workflow.tasks) == 7
