"""project_context.md merge tests (§4.3)."""

from __future__ import annotations

from pathlib import Path

from vespawd_executor.parse.context_updates import parse_context_updates
from vespawd_executor.parse.sections import get_section, split_sections
from vespawd_executor.sync.project_context import merge_project_context

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SAMPLE = (FIXTURES / "sample_master_prompt.md").read_text(encoding="utf-8")


def test_merge_updates_existing_fields(tmp_path: Path) -> None:
    path = tmp_path / "project_context.md"
    path.write_text(
        "# Project Context\n\n"
        "## Product\n\n"
        "- **Name:** oldname\n\n"
        "## Layout\n\n"
        "| Field | Value |\n"
        "|-------|--------|\n"
        "| Mode | integrated |\n"
        "| POS folder (sidecar) | - |\n"
        "| Application code | `src/` |\n\n"
        "## Tech Stack\n\n"
        "| Area | Choice |\n"
        "|------|--------|\n"
        "| Database | SQLite |\n",
        encoding="utf-8",
    )
    section_map, _ = split_sections(SAMPLE)
    assert section_map
    updates = parse_context_updates(get_section(section_map.sections, "PROJECT CONTEXT UPDATES"))
    merge_project_context(path, updates)
    text = path.read_text(encoding="utf-8")
    assert "**Name:** CourseReg" in text
    assert "sidecar" in text
    assert "integrated" not in text
    assert "main/src/" in text
    assert "MySQL" in text


def test_merge_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "project_context.md"
    section_map, _ = split_sections(SAMPLE)
    updates = parse_context_updates(get_section(section_map.sections, "PROJECT CONTEXT UPDATES"))
    merge_project_context(path, updates)
    first = path.read_text(encoding="utf-8")
    merge_project_context(path, updates)
    second = path.read_text(encoding="utf-8")
    assert first == second


def test_merge_preserves_unrelated_sections(tmp_path: Path) -> None:
    path = tmp_path / "project_context.md"
    path.write_text(
        "# Project Context\n\n## Links\n\n- CI: https://ci.example\n\n## Product\n\n- **Name:** x\n",
        encoding="utf-8",
    )
    section_map, _ = split_sections(SAMPLE)
    updates = parse_context_updates(get_section(section_map.sections, "PROJECT CONTEXT UPDATES"))
    merge_project_context(path, updates)
    text = path.read_text(encoding="utf-8")
    assert "https://ci.example" in text
