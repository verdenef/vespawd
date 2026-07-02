"""Worker registry and discovery tests."""

from pathlib import Path

from vedaws.config.loader import load_config
from vedaws.workers import WorkerType, discover_workers
from vedaws.workers.registry import WorkerRegistry


def test_discovers_bundled_workers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = load_config(tmp_path)
    result = discover_workers(config)
    ids = {worker.id for worker in result.workers}
    assert "human.default" in ids
    assert "ai.claude" in ids
    assert "tool.git" in ids


def test_registry_lookup_by_capability(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = load_config(tmp_path)
    result = discover_workers(config)
    registry = WorkerRegistry.from_discovery(result)

    codegen_workers = registry.find_by_capability("code-generation")
    assert len(codegen_workers) >= 2
    assert all(w.metadata.worker_type == WorkerType.AI for w in codegen_workers)

    git_workers = registry.find_by_capability("version-control", scope="repository")
    assert len(git_workers) == 1
    assert git_workers[0].id == "tool.git"


def test_registry_list_by_type(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = load_config(tmp_path)
    registry = WorkerRegistry.from_discovery(discover_workers(config))

    assert len(registry.list_by_type(WorkerType.HUMAN)) >= 1
    assert len(registry.list_by_type(WorkerType.AI)) >= 3
    assert len(registry.list_by_type(WorkerType.TOOL)) >= 4


def test_invalid_manifest_recorded(tmp_path: Path, monkeypatch) -> None:
    bad_dir = tmp_path / "bad-workers" / "broken"
    bad_dir.mkdir(parents=True)
    (bad_dir / "vedaws.worker.toml").write_text("not valid toml [[[", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VEDAWS_WORKER_PATHS", str(tmp_path / "bad-workers"))
    result = discover_workers(load_config(tmp_path))
    assert len(result.invalid) >= 1


def test_duplicate_ids_recorded(tmp_path: Path, monkeypatch) -> None:
    dup_root = tmp_path / "dup-workers"
    for name in ("a", "b"):
        worker_dir = dup_root / name
        worker_dir.mkdir(parents=True)
        (worker_dir / "vedaws.worker.toml").write_text(
            """
[worker]
id = "duplicate.test"
name = "Dup"
version = "0.1.0"
type = "tool"

[[capabilities]]
work_type = "test"
""".strip(),
            encoding="utf-8",
        )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VEDAWS_WORKER_PATHS", str(dup_root))
    result = discover_workers(load_config(tmp_path))
    assert len(result.duplicates) == 1
    assert result.worker_count == 1
