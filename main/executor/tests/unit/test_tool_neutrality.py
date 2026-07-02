"""Tool neutrality verification (Executor Spec §14).

The Executor must be IDE-neutral and interact with the Bridge only via its public
CLI. These checks enforce that at the source level: no library module imports the
Bridge internals or any vendor IDE SDK.
"""

from __future__ import annotations

import ast
from pathlib import Path

LIB_ROOT = Path(__file__).resolve().parents[2] / "lib" / "vespawd_executor"

# §14 / §8: Bridge is invoked via subprocess CLI only; vendor IDE SDKs are forbidden.
_FORBIDDEN_IMPORT_ROOTS = {
    "vespawd_bridge",  # ownership boundary — CLI only
    "vedaws",  # CLI subprocess only (§9)
    "cursor",
    "windsurf",
    "copilot",
    "jetbrains",
}


def _module_files() -> list[Path]:
    return sorted(LIB_ROOT.rglob("*.py"))


def _imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                roots.add(node.module.split(".")[0])
    return roots


def test_no_forbidden_imports_anywhere() -> None:
    offenders: dict[str, set[str]] = {}
    for path in _module_files():
        bad = _imported_roots(path) & _FORBIDDEN_IMPORT_ROOTS
        if bad:
            offenders[str(path.relative_to(LIB_ROOT))] = bad
    assert not offenders, f"Forbidden imports found (§14): {offenders}"


def test_bridge_only_via_subprocess() -> None:
    client = LIB_ROOT / "bridge" / "client.py"
    tree = ast.parse(client.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    assert "subprocess" in roots
    assert "vespawd_bridge" not in roots


def test_report_has_no_vendor_terminology() -> None:
    from vespawd_executor.reporting.report import build_report

    md = build_report(changed=["main/src/a.py"], handoff_ready=True, handoff_current=True).to_markdown()
    lowered = md.lower()
    for vendor in ("cursor", "windsurf", "copilot", "jetbrains", "vscode"):
        assert vendor not in lowered
