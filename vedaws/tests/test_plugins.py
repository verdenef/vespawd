"""Plugin discovery tests."""

from pathlib import Path

from vedaws.config.loader import load_config
from vedaws.plugins.discovery import discover_plugins
from vedaws.plugins.validation import validate_manifest
from vedaws.plugins.sdk import PluginContext, VedawsPlugin
from vedaws.runtime.bootstrap import bootstrap


def test_discovers_bundled_hello_plugin(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = load_config(tmp_path)
    result = discover_plugins(config)
    ids = {plugin.id for plugin in result.plugins}
    assert "hello" in ids


def test_discovers_plugin_in_custom_path(tmp_path: Path, monkeypatch) -> None:
    plugin_dir = tmp_path / "custom-plugins" / "sample"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "sample_plugin.py").write_text(
        """
from vedaws.plugins.sdk import PluginContext, VedawsPlugin

class SamplePlugin(VedawsPlugin):
    def register(self, context: PluginContext) -> None:
        pass
""".strip(),
        encoding="utf-8",
    )
    (plugin_dir / "vedaws.plugin.toml").write_text(
        """
[plugin]
id = "sample"
name = "Sample"
version = "1.0.0"
entry_point = "sample_plugin:SamplePlugin"
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VEDAWS_PLUGIN_PATHS", str(tmp_path / "custom-plugins"))
    config = load_config(tmp_path)
    result = discover_plugins(config)
    assert any(plugin.id == "sample" for plugin in result.plugins)


def test_invalid_manifest_reported(tmp_path: Path, monkeypatch) -> None:
    plugin_dir = tmp_path / "bad"
    plugin_dir.mkdir()
    (plugin_dir / "vedaws.plugin.toml").write_text(
        '[plugin]\nid = "bad"\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VEDAWS_PLUGIN_PATHS", str(plugin_dir))
    config = load_config(tmp_path)
    result = discover_plugins(config)
    assert result.invalid
    assert not any(plugin.id == "bad" for plugin in result.plugins)


def test_hello_plugin_activates_on_bootstrap(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    context = bootstrap(tmp_path)
    hello = context.registry.get("hello")
    assert hello is not None
    assert hello.is_active
    assert context.worker_registry.get("hello.worker") is not None


def test_plugin_manifest_security_validation_rejects_unknown_permission(
    tmp_path: Path, monkeypatch
) -> None:
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
permissions = ["subprocess.magic"]
network = "none"
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VEDAWS_PLUGIN_PATHS", str(tmp_path / "custom-plugins"))
    config = load_config(tmp_path)
    discovery = discover_plugins(config)
    target = next((manifest for manifest in discovery.plugins if manifest.id == "badsec"), None)
    assert target is not None
    errors = validate_manifest(target)
    assert errors
    assert any("unknown security permissions" in error for error in errors)
