"""Unit tests — phase map (§11.1)."""

from __future__ import annotations

from vespawd_bridge.manifest.model import PhaseMapEntry
from vespawd_bridge.manifest.phase_map import resolve_phase

PHASE_MAP = (
    PhaseMapEntry("implement", ("implement", "feature", "build")),
    PhaseMapEntry("scope", ("scope", "requirements")),
)


def test_resolve_phase_keyword() -> None:
    task_id, fallback = resolve_phase("Build the feature", None, None, PHASE_MAP)
    assert task_id == "software.implement"
    assert fallback is False


def test_resolve_phase_fallback() -> None:
    task_id, fallback = resolve_phase("unknown work", None, None, PHASE_MAP)
    assert task_id == "software.scope"
    assert fallback is True
