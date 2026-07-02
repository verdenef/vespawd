"""HANDOFF seed tests (§5.3 step 4, §13.1)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from vespawd_executor.parse import parse_master_prompt
from vespawd_executor.sync.handoff import seed_handoff

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SAMPLE = (FIXTURES / "sample_master_prompt.md").read_text(encoding="utf-8")


def test_seed_handoff_fills_empty_sections(tmp_path: Path) -> None:
    path = tmp_path / "HANDOFF.md"
    result = parse_master_prompt(SAMPLE)
    assert result.ok and result.parsed
    seed_handoff(
        path,
        result.parsed,
        repo_path="/repo/vespawd",
        timestamp=datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    text = path.read_text(encoding="utf-8")
    assert "CourseReg" in text
    assert "Phase goal:" in text
    assert "Repo: /repo/vespawd" in text
    assert "Last updated:" in text


def test_seed_preserves_existing_what_built(tmp_path: Path) -> None:
    path = tmp_path / "HANDOFF.md"
    path.write_text(
        """# Handoff

## Project

- **Name:** Old

## What was built

- Existing feature shipped

---

_Generated: old | Repo: old_
""",
        encoding="utf-8",
    )
    result = parse_master_prompt(SAMPLE)
    assert result.parsed
    seed_handoff(path, result.parsed, repo_path="/repo")
    text = path.read_text(encoding="utf-8")
    assert "Existing feature shipped" in text
    assert "Phase goal:" not in text
