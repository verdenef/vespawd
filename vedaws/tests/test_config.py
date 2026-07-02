"""Configuration loading tests."""

from pathlib import Path

import pytest

from vedaws.config.loader import apply_plugin_configuration, load_config, load_project_section
from vedaws.project.init import init_project
from vedaws.runtime.bootstrap import bootstrap


def test_default_config_has_logging_and_plugins(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = load_config(tmp_path)
    assert config.logging.level == "INFO"
    assert config.plugins.enabled is True
    assert config.runtime.name == "vedaws"
    assert config.security.allow_env_secrets is True
    assert config.security.allow_file_secrets is False


def test_environment_overrides_log_level(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VEDAWS_LOG_LEVEL", "DEBUG")
    config = load_config(tmp_path)
    assert config.logging.level == "DEBUG"


def test_project_config_overrides_user_defaults(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path, name="demo")
    project_config = tmp_path / ".vedaws" / "config.toml"
    project_config.write_text(
        """
[logging]
level = "WARNING"

[runtime]
name = "demo-runtime"
""".strip(),
        encoding="utf-8",
    )
    config = load_config(tmp_path)
    assert config.logging.level == "WARNING"
    assert config.runtime.name == "demo-runtime"


def test_load_project_section_after_init(tmp_path: Path) -> None:
    init_project(tmp_path, name="alpha")
    section = load_project_section(tmp_path)
    assert section is not None
    assert section.name == "alpha"
    assert section.state == "created"  # project.toml mirror field


def test_security_config_parsing_and_env_override(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path, name="secure")
    project_config = tmp_path / ".vedaws" / "config.toml"
    project_config.write_text(
        """
[security]
allow_env_secrets = false
allow_file_secrets = true
""".strip()
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("VEDAWS_ALLOW_ENV_SECRETS", "true")
    config = load_config(tmp_path)
    assert config.security.allow_env_secrets is True
    assert config.security.allow_file_secrets is True


def test_apply_plugin_configuration_merges_defaults_into_extensions() -> None:
    config = load_config(Path.cwd())
    config.extensions["hello"] = {}
    merged = apply_plugin_configuration(
        config,
        {
            "hello": {
                "message": {
                    "type": "string",
                    "default": "Hello from schema",
                    "description": "Greeting",
                }
            }
        },
    )
    assert merged.extensions["hello"]["message"] == "Hello from schema"


def test_apply_plugin_configuration_rejects_invalid_type() -> None:
    config = load_config(Path.cwd())
    config.extensions["hello"] = {"message": 123}
    with pytest.raises(ValueError):
        apply_plugin_configuration(
            config,
            {
                "hello": {
                    "message": {
                        "type": "string",
                        "default": "ok",
                    }
                }
            },
        )


def test_bootstrap_applies_plugin_configuration_defaults(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    context = bootstrap(tmp_path)
    assert context.config.extensions["hello"]["message"] == "Hello, Vedaws!"
