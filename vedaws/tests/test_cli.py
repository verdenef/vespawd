"""CLI tests."""

from pathlib import Path

from vedaws.cli.app import main


def test_version_command() -> None:
    assert main(["version"]) == 0


def test_init_and_status_commands(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["init", str(tmp_path), "--name", "cli-demo"]) == 0
    assert main(["status", str(tmp_path)]) == 0


def test_doctor_warns_without_project(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["doctor", str(tmp_path)]) == 0


def test_doctor_passes_with_project(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", str(tmp_path)])
    assert main(["doctor", str(tmp_path)]) == 0


def test_status_accepts_path_flag(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", str(tmp_path)])
    assert main(["status", "--path", str(tmp_path)]) == 0


def test_doctor_accepts_path_flag(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", str(tmp_path)])
    assert main(["doctor", "--path", str(tmp_path)]) == 0


def test_events_accepts_path_flag(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", str(tmp_path)])
    assert main(["events", "--path", str(tmp_path)]) == 0


def test_doctor_reports_plugin_security_check(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", str(tmp_path)])
    assert main(["doctor", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "plugin security" in output


def test_workers_command_lists_registered_workers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["workers", "--path", str(tmp_path)]) == 0


def test_state_command_requires_project(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["state", "--path", str(tmp_path)]) == 1


def test_state_and_history_after_init(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", str(tmp_path), "--name", "state-cli"])
    assert main(["state", "--path", str(tmp_path)]) == 0
    assert main(["state", "history", "--path", str(tmp_path)]) == 0


def test_state_transition_command(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", str(tmp_path)])
    assert main(["state", "transition", "initialized", "--path", str(tmp_path)]) == 0
    assert main(["state", "--path", str(tmp_path)]) == 0


def test_workflow_command_lists_definitions(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", str(tmp_path)])
    assert main(["workflow", "--path", str(tmp_path)]) == 0


def test_workflow_activate_and_tasks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", str(tmp_path)])
    main(["state", "transition", "initialized", "--path", str(tmp_path)])
    assert main(["workflow", "activate", "default", "--path", str(tmp_path)]) == 0
    assert main(["tasks", "--path", str(tmp_path)]) == 0
    assert main(["tasks", "complete", "default.plan", "--path", str(tmp_path)]) == 0


def test_run_command_executes_workflow(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", str(tmp_path)])
    main(["state", "transition", "initialized", "--path", str(tmp_path)])
    main(["workflow", "activate", "default", "--path", str(tmp_path)])
    assert main(["run", "--path", str(tmp_path)]) == 0


def test_workers_run_command(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    main(["init", str(tmp_path)])
    main(["state", "transition", "initialized", "--path", str(tmp_path)])
    main(["workflow", "activate", "default", "--path", str(tmp_path)])
    assert main(["workers", "run", "mock.success", "--path", str(tmp_path)]) == 0
