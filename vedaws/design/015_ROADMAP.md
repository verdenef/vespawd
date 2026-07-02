# Roadmap

**Version:** 0.5.0

**Status:** Living — updated at architecture milestones

## Purpose

This document records the **architectural roadmap** for Vedaws: what is complete at v0.5 freeze, what is prioritized before v1, and what remains explicitly deferred.

It derives from [`ARCHITECTURE_REVIEW_V0.5.md`](../docs/ARCHITECTURE_REVIEW_V0.5.md) and [`ARCHITECTURE_FREEZE_V0.5.md`](../docs/ARCHITECTURE_FREEZE_V0.5.md). It does not invent new milestones beyond those proposed in the review.

---

## v0.5 freeze (complete)

Architecture v0.5 is **frozen** as of [`ARCHITECTURE_FREEZE_V0.5.md`](../docs/ARCHITECTURE_FREEZE_V0.5.md). The orchestration spine and extension model through Milestone 12 are the baseline for all subsequent work.

**Overall architecture score at review:** 7.8 / 10  
**v1 production readiness at review:** 5.5 / 10

---

## Completed milestones

| Milestone | Deliverable | Design reference |
|-----------|-------------|------------------|
| Sprint 1–5 / M5.5 | Core runtime, state, workflow, workers, dispatch | `003_RUNTIME.md`, `006_STATE_MACHINE.md`, `004_WORKERS.md` |
| M6 | Plugin platform + Git plugin | `010_PLUGINS.md` |
| M7 | Event bus | `003_RUNTIME.md` |
| M8 | Event integration (workflow, dispatch, plugins) | `003_RUNTIME.md` |
| M9 | Software domain plugin | `008_ARTIFACTS.md` |
| M10 | Unity domain plugin | `008_ARTIFACTS.md` |
| M11 | Automation engine | `005_AUTOMATION.md` |
| M12 | AI provider SDK + mock-ai | `017_AI_PROVIDERS.md` |

Historical implementation detail: `docs/MILESTONE_6_SUMMARY.md` through `docs/MILESTONE_12_SUMMARY.md`.

---

## Reprioritized before v1

Per architecture review §Recommended roadmap changes. M13–M16 are now implemented; remaining items are v1+ backlog.

### M13 — AI Worker Binding (P0)

Connect `AIService` to the `ExecutableWorker` execution path. Workflow tasks request AI capabilities; `mock-ai` validates end-to-end before vendor plugins.

**Depends on:** Frozen `TaskDispatch` / `TaskOutcome` contract, `017_AI_PROVIDERS.md`

**Status:** Complete — `AIExecutableWorker` executes through `AIService` with capability routing.

### M14 — Security & Trust (P0)

Plugin permissions manifest, subprocess policy, secrets interface (availability hooks first). Implements direction sketched in `013_SECURITY.md`.

**Depends on:** Frozen plugin platform (`010_PLUGINS.md`)

**Status:** Complete — permission declarations, validation hooks, doctor reporting, and security config availability shipped in Milestone 14.

### M15 — Orchestration Hardening (P1)

Deterministic run-loop hardening, improved dispatcher diagnostics, `detect_project(read_only=True)`, and state-sync side-effect reduction (`project.toml` vs `state.toml`) while preserving synchronous execution.

**Depends on:** Frozen synchronous orchestration model documented as interim

**Status:** Complete — deterministic run-loop hardening, dispatch diagnostics, and read-only project detection shipped in Milestone 15.

### M16 — Skills & Config (P1)

Implement skill execution binding and plugin config schema merge while preserving capability-based dispatch and plugin-owned extensions.

**Depends on:** M13 for skill-guided AI worker execution path

**Status:** Complete — skills are runtime-consumable at worker execution time and plugin configuration schemas are merged/validated during bootstrap.

### Architecture v1.0 freeze milestone

Public API audit, semver policy for `vedaws.plugin.toml`, workflow TOML, and `TaskDispatch` contract. [`API_STABILITY.md`](../docs/API_STABILITY.md) exists at v0.5; v1 freeze extends and hardens it.

---

## P0 / P1 / P2 backlog (from review)

| Priority | Item | Target milestone |
|----------|------|------------------|
| P0 | AI worker binding | M13 |
| P0 | Security model + plugin trust boundaries | M14 |
| P0 | Align package version with architecture `0.5.0` | Release tag |
| P1 | Skills execution binding (first runtime consumer) | M16 |
| P1 | Plugin config schema merge + validation | M16 |
| P1 | Doctor unit tests + hello command handler fix | M15 or patch |
| P1 | Remove write-on-read from `detect_project` | M15 |
| P1 | Dispatch/job model for long-running work | M15 |
| P2 | Event payload schemas | Post-M15 |
| P2 | `.vedaws/` schema versioning | Post-M15 |
| P2 | Artifact registry or formalize plugin-owned artifacts | Post-M16 |
| P2 | Promote remaining draft design docs to Active | Ongoing doc sprint |

---

## Explicitly deferred (unchanged)

Do not schedule these before v1 foundations above unless architecture review says otherwise:

| Item | Rationale |
|------|-----------|
| Distributed execution / multi-node runtime | v2-scale; synchronous bus frozen for v0.5 |
| MCP in core | Keep plugin-local (`017_AI_PROVIDERS.md`) |
| Memory system | `009_MEMORY.md` — after AI workers produce retrievable context |
| Streaming UI / IDE shell | Separate front-end; CLI remains scriptable |
| Scheduling / background automation | Deferred in `005_AUTOMATION.md` |
| Remote plugin registry / signed bundles | Deferred in `010_PLUGINS.md` |
| Additional domain plugins | Review: do **not** add before M13 — repeats placeholder pattern |

---

## Anti-patterns (post-freeze)

1. **More domain plugins before AI worker binding** — does not increase core value.
2. **Domain logic in `runtime/vedaws/`** — violates frozen plugin-only model.
3. **Vendor SDK imports in core** — violates `AIProvider` routing invariant.
4. **Implicit memory or state** — violates philosophy; use explicit `.vedaws/` files.

---

## Relationship to other documents

| Document | Relationship |
|----------|--------------|
| `016_IMPLEMENTATION_PLAN.md` | Milestone deliverables and sequencing |
| `000_VISION.md` | Long-term vision; memory and health remain future |
| [`docs/ARCHITECTURE_FREEZE_V0.5.md`](../docs/ARCHITECTURE_FREEZE_V0.5.md) | Frozen decisions this roadmap must not contradict |
| [`docs/API_STABILITY.md`](../docs/API_STABILITY.md) | Public contracts milestones must preserve or version |

---

## TODO

- Update after each milestone (M13+) with completion status and score reassessment
- Add dates/owners when project management process is defined
