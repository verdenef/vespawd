# Implementation Plan

**Version:** 0.5.0

**Status:** Living — high-level strategy through v1

## Purpose

This document describes **how Vedaws is implemented** relative to the architecture: milestone sequencing, deliverable expectations, and the rule that design documents stay synchronized with code.

It complements `015_ROADMAP.md` (what to build) with execution conventions (how milestones land in the repository).

Source: [`ARCHITECTURE_REVIEW_V0.5.md`](../docs/ARCHITECTURE_REVIEW_V0.5.md), [`ARCHITECTURE_FREEZE_V0.5.md`](../docs/ARCHITECTURE_FREEZE_V0.5.md).

---

## Implementation principles

1. **Architecture first** — update `design/` in the same milestone as intentional implementation changes (`design/README.md` rules).
2. **Domain neutrality** — new domain behavior ships as plugins under `plugins/`, not in `runtime/vedaws/`.
3. **Integration tests** — milestones add or extend tests under `tests/`; 107 tests at v0.5 review baseline.
4. **No silent drift** — if code contradicts design, fix design or code in the same change set.
5. **Freeze respect** — post-M12 work must not break decisions in [`ARCHITECTURE_FREEZE_V0.5.md`](../docs/ARCHITECTURE_FREEZE_V0.5.md) without review.

---

## v0.5 freeze gate (complete)

| Gate | Status |
|------|--------|
| M6–M12 implementation | Complete |
| Architecture review | `docs/ARCHITECTURE_REVIEW_V0.5.md` |
| Freeze declaration | `docs/ARCHITECTURE_FREEZE_V0.5.md` |
| API stability reference | `docs/API_STABILITY.md` |
| Design stub completion (009, 013–016) | Complete (Architecture Freeze sprint) |
| Design index alignment (README, headers, M12 docs) | Complete (Architecture Freeze sprint) |

---

## Repository targets per layer

| Layer | Path | Milestone introduced |
|-------|------|----------------------|
| Runtime core | `runtime/vedaws/` | Sprint 1–5 |
| Plugins | `plugins/<id>/` | M6+ |
| Tests | `tests/test_*.py` | Per subsystem |
| Design | `design/*.md` | Continuous |
| Milestone records | `docs/MILESTONE_*_SUMMARY.md` | Per milestone |

Layout detail: `014_REPOSITORY.md`.

---

## Proposed milestones (post-freeze)

### M13 — AI Worker Binding

**Goal:** Workers invoke `AIService` during `execute()` when task capability maps to an AI capability.

| Deliverable | Location (expected) |
|-------------|---------------------|
| Worker ↔ AI integration wiring | `runtime/vedaws/workers/` and/or `runtime/vedaws/ai/` |
| Workflow capability mapping | `runtime/vedaws/dispatch/` or workflow models |
| mock-ai worker path | `plugins/mock-ai/` |
| Design update | `004_WORKERS.md`, `017_AI_PROVIDERS.md` |
| Tests | `tests/test_ai_providers.py`, dispatch/workflow tests |

**Exit criteria:** At least one workflow task dispatches to an AI-capable worker using `mock-ai`; no vendor imports in core.

---

### M14 — Security & Trust

**Goal:** Documented and enforced trust boundaries beyond activation toggles.

| Deliverable | Location (expected) |
|-------------|---------------------|
| Permission manifest schema | `design/013_SECURITY.md`, `010_PLUGINS.md` |
| Subprocess policy hooks | Runtime doctor + plugin validation |
| Secrets availability interface | `012_CONFIGURATION.md`, `runtime/vedaws/config/` |
| Design promotion | `013_SECURITY.md` → Active when implemented |
| Tests | `tests/test_plugins*.py`, new security-focused tests |

**Exit criteria:** Doctor reports permission violations; Git plugin compatible with declared permissions.

**Milestone status update:** Implemented in M14 with additive plugin security declarations (`[security]`), validation hooks, doctor security checks, and runtime security config for secrets availability.

---

### M15 — Orchestration Hardening

**Goal:** Harden synchronous orchestration reliability and diagnosability without redesigning frozen contracts.

| Deliverable | Location (expected) |
|-------------|---------------------|
| Deterministic dispatch/run-loop resilience | `runtime/vedaws/dispatch/` |
| `detect_project(read_only=True)` | `runtime/vedaws/project/detector.py` |
| State sync fixes | `runtime/vedaws/project/` |
| Design update | `003_RUNTIME.md`, `007_PROJECT_MODEL.md` |
| Tests | `tests/test_dispatch.py`, `tests/test_state*.py` |

**Exit criteria:** Run-loop behavior is deterministic under partial failures, orchestration diagnostics improve, and manifest write-on-read is removed or explicitly gated.

**Milestone status update:** Implemented in M15 with deterministic run-loop retries/diagnostics and read-only project detection during bootstrap.

---

### M16 — Skills & Config

**Goal:** Implement the remaining ghost APIs as additive, stable behavior.

| Deliverable | Location (expected) |
|-------------|---------------------|
| Skill execution binding | `011_SKILLS.md`, `workers/ai_worker.py`, workflow models |
| Config schema merge + validation | `012_CONFIGURATION.md`, `config/loader.py` |
| Design update | `010_PLUGINS.md`, `API_STABILITY.md` |
| Tests | Plugin and config tests |

**Exit criteria:** `contribute_skill()` and `contribute_configuration()` both provide functional runtime behavior without breaking existing configs/plugins.

**Milestone status update:** Implemented in M16 with AI worker skill-guidance binding and bootstrap-time plugin configuration schema merge/validation.

---

### v1.0 architecture freeze milestone

| Deliverable | Location |
|-------------|----------|
| Extended API stability audit | `docs/API_STABILITY.md` |
| Semver policy for file formats | `docs/` + `design/010_PLUGINS.md` |
| Design doc promotion | Draft → Active where implementation matches |

---

## Test expectations by area

| Area | Test files (v0.5) | Review assessment |
|------|---------------------|-------------------|
| Plugins | `test_plugins.py`, `test_plugins_platform.py`, domain plugin tests | Strong (~33) |
| Workflow / state / dispatch | `test_workflow.py`, `test_state.py`, `test_dispatch.py` | Strong (~27) |
| Events / automation / AI | `test_event_bus.py`, `test_automation.py`, `test_ai_providers.py` | Strong (~30) |
| Doctor | Smoke via CLI only | Weak — dedicated tests P1 |
| Bootstrap | `test_bootstrap.py` (2 tests) | Weak |
| Hello plugin CLI | None | Gap |

New milestones should add meaningful integration coverage, not trivial assertions.

---

## Milestone documentation checklist

Each implementation milestone should produce:

1. Updated design document(s) in `design/`
2. `docs/MILESTONE_<N>_SUMMARY.md` (historical record)
3. Tests in `tests/`
4. If public APIs change: update `docs/API_STABILITY.md`
5. If frozen decisions change: architecture review per `.ai/architect_escalation.md`

---

## What not to implement without review

| Request | Escalation trigger |
|---------|-------------------|
| New core concept in `002_CORE.md` | New core concept |
| Async event bus replacing sync semantics | Runtime change + v2-scale |
| MCP in `runtime/vedaws/` | Domain neutrality / new core integration |
| Memory store APIs | `009_MEMORY.md` — prerequisites not met |
| Fourth domain plugin before M13 | Roadmap anti-pattern |

---

## Relationship to other documents

| Document | Relationship |
|----------|--------------|
| `015_ROADMAP.md` | Priority and deferral list |
| `014_REPOSITORY.md` | Where code lives |
| `design/README.md` | Architecture index and layer diagram |

---

## TODO

- Keep milestone status text synchronized after each milestone lands
- Record actual milestone dates and commit references in `docs/MILESTONE_*_SUMMARY.md`
