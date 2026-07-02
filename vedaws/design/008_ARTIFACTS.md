# Artifacts

**Version:** 0.5.0

**Status:** Active — v0.5 freeze (software and Unity template artifacts; Milestones 9–10)

## Purpose

**Artifacts** are durable project outputs produced and consumed during orchestration. The runtime core does not own artifact content — it tracks lifecycle through workflows, tasks, and events. Domain plugins define artifact types, paths, and conventions.

---

## Core Model

| Concept | Owner |
|---------|-------|
| Artifact paths & types | Domain plugins |
| Artifact presence checks | Plugin commands / workers |
| Workflow task linkage | Plugin workflow definitions |
| Content validation | Humans, workers, future AI providers |

Artifacts live in the **project workspace** (outside `.vedaws/` for domain template projects), not in runtime configuration.

---

## Software Artifacts (Software Workflow Plugin)

Standard paths scaffolded by `vedaws init software`:

| Artifact | Path | Typical task |
|----------|------|--------------|
| Architecture | `docs/architecture/ARCHITECTURE.md` | architecture |
| API | `docs/api/API.md` | api-design, implement |
| Decisions | `docs/decisions/DECISIONS.md` | test, review |
| Handoff | `docs/handoff/HANDOFF.md` | handoff |

Each directory includes a `README.md` index. Workers append completion markers; `vedaws software artifacts` reports presence.

---

## Unity Artifacts (Unity Game Development Plugin)

Standard paths scaffolded by `vedaws init unity`:

| Artifact | Path | Typical task |
|----------|------|--------------|
| Game design | `Docs/game-design/GAME_DESIGN.md` | concept, game-design |
| Technical design | `Docs/technical-design/TECHNICAL_DESIGN.md` | prototype, gameplay, ui |
| Builds | `Docs/builds/README.md` | build, release |
| Playtests | `Docs/playtests/PLAYTEST_LOG.md` | testing |

Unity projects also scaffold `Assets/`, `Packages/`, and `ProjectSettings/` as layout directories (no Unity Editor binary). Each `Docs/` subdirectory includes a `README.md` index. `vedaws unity status` reports layout and artifact presence.

---

## CLI

```bash
vedaws software artifacts    # checklist with ok/missing
vedaws software status       # artifacts + workflow progress
vedaws unity status          # layout + documentation artifacts + workflow progress
```

---

## Event Integration

Domain plugins subscribe to `TaskCompleted` and `WorkflowCompleted` via the Plugin SDK to observe artifact-related task progress (logging today; automation hooks deferred).

---

## v0.5 freeze boundary

| Surface | Status at v0.5 |
|---------|----------------|
| Plugin-defined artifact paths (software, Unity) | **Implemented** |
| CLI presence checks (`software artifacts`, `unity status`) | **Implemented** |
| Runtime artifact content ownership | **Not in core** — plugins own types and paths |
| Generic artifact registry in runtime | **Deferred** (review P2) |
| Provenance / dispatch audit linkage | **Deferred** |

Frozen model: artifacts live in the **project workspace**; orchestration references them through plugin workers and commands, not a central runtime registry.

---

## Future

- Artifact schema validation in plugin workers
- AI-generated content written to standard paths
- Cross-plugin artifact type registry

---

## TODO

- Generic artifact registry in runtime — deferred; plugins own types at v0.5 (`015_ROADMAP.md` P2).
- Provenance tracking linked to dispatch audit log — deferred (dispatch audit not implemented).
- Artifact schema validation in plugin workers — future domain plugin work.
