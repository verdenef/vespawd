"""Default phase map (Bridge Spec §4.2)."""

from __future__ import annotations

from vespawd_bridge.manifest.model import PhaseMapEntry

DEFAULT_PHASE_MAP: tuple[PhaseMapEntry, ...] = (
    PhaseMapEntry("scope", ("scope", "requirements", "mvp")),
    PhaseMapEntry("architecture", ("architecture", "components", "adr")),
    PhaseMapEntry("api-design", ("api", "schema", "contracts")),
    PhaseMapEntry("implement", ("implement", "feature", "build")),
    PhaseMapEntry("test", ("test", "verify", "demo")),
    PhaseMapEntry("review", ("review", "lint", "fix pass")),
    PhaseMapEntry("handoff", ("handoff", "submission package")),
)


def resolve_phase(
    goal: str,
    notes: str | None,
    phase_hint: str | None,
    phase_map: tuple[PhaseMapEntry, ...],
    force_phase: str | None = None,
) -> tuple[str, bool]:
    """Return (vedaws_task_id e.g. software.implement, used_fallback)."""
    if force_phase:
        task_id = force_phase.removeprefix("software.")
        return f"software.{task_id}", False

    if phase_hint:
        hint = phase_hint.strip().removeprefix("software.")
        for entry in phase_map:
            if entry.task_id == hint or hint in entry.keywords:
                return f"software.{entry.task_id}", False
        if hint:
            return f"software.{hint}", True

    haystack = f"{goal}\n{notes or ''}".lower()
    for entry in phase_map:
        for keyword in entry.keywords:
            if keyword.lower() in haystack:
                return f"software.{entry.task_id}", False

    return "software.scope", True
