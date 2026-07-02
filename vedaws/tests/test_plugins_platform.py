"""Plugin platform lifecycle and CLI tests."""

from pathlib import Path

from vedaws.cli.app import main
from vedaws.plugins.activation import load_activation_config
from vedaws.plugins.dependencies import resolve_dependencies
from vedaws.plugins.lifecycle import PluginStatus
from vedaws.plugins.manifest import PluginDependency, PluginManifest
from vedaws.project.init import init_project
from vedaws.runtime.bootstrap import bootstrap


def test_plugin_dependency_resolution_detects_cycles() -> None:
    manifests = {
        "a": PluginManifest(
            id="a",
            name="A",
            version="1.0.0",
            entry_point="a:A",
            dependencies=(PluginDependency(id="b"),),
        ),
        "b": PluginManifest(
            id="b",
            name="B",
            version="1.0.0",
            entry_point="b:B",
            dependencies=(PluginDependency(id="a"),),
        ),
    }
    result = resolve_dependencies(manifests, selected_ids={"a", "b"})
    assert not result.ok
    assert any("Circular" in error for error in result.errors)


def test_project_init_writes_plugins_toml(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config_dir = init_project(tmp_path, name="plugin-demo")
    plugins_path = config_dir / "plugins.toml"
    assert plugins_path.is_file()
    activation = load_activation_config(plugins_path)
    assert "hello" in activation.enabled
    assert "git" in activation.enabled


def test_plugins_cli_list_and_info(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    assert main(["plugins", "list", "--path", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "hello" in output

    assert main(["plugins", "info", "hello", "--path", str(tmp_path)]) == 0
    info_output = capsys.readouterr().out
    assert "hello.worker" in info_output


def test_plugins_disable_prevents_activation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    assert main(["plugins", "disable", "hello", "--path", str(tmp_path)]) == 0
    context = bootstrap(tmp_path)
    hello = context.registry.get("hello")
    assert hello is not None
    assert hello.status == PluginStatus.DISABLED
    assert context.worker_registry.get("hello.worker") is None


def test_plugins_enable_restores_activation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    main(["plugins", "disable", "hello", "--path", str(tmp_path)])
    assert main(["plugins", "enable", "hello", "--path", str(tmp_path)]) == 0
    context = bootstrap(tmp_path)
    hello = context.registry.get("hello")
    assert hello is not None
    assert hello.is_active


def test_security_validation_blocks_plugin_activation(tmp_path: Path, monkeypatch) -> None:
    plugin_dir = tmp_path / "custom-plugins" / "badsec"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "bad_plugin.py").write_text(
        """
from vedaws.plugins.sdk import PluginContext, VedawsPlugin

class BadPlugin(VedawsPlugin):
    def register(self, context: PluginContext) -> None:
        pass
""".strip(),
        encoding="utf-8",
    )
    (plugin_dir / "vedaws.plugin.toml").write_text(
        """
[plugin]
id = "badsec"
name = "Bad Security Plugin"
version = "1.0.0"
entry_point = "bad_plugin:BadPlugin"
manifest_version = "1"

[security]
permissions = ["unknown.permission"]
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VEDAWS_PLUGIN_PATHS", str(tmp_path / "custom-plugins"))
    context = bootstrap(tmp_path)
    record = context.registry.get("badsec")
    assert record is not None
    assert record.status == PluginStatus.FAILED
    assert record.error is not None
    assert "unknown security permissions" in record.error
