# Memory

**Version:** 0.5.0

**Status:** Deferred — out of v0.5 freeze scope

## Purpose

**Memory** is the long-term architectural concept for retaining and retrieving project context across sessions, workers, and AI interactions — without relying on implicit conversation history or undocumented assumptions.

`000_VISION.md` lists memory among Vedaws responsibilities. At architecture v0.5 freeze, **no memory subsystem is implemented** in the runtime. This document records the deferral boundary so contributors do not assume memory APIs exist.

---

## v0.5 freeze boundary

| Area | Status at v0.5 |
|------|----------------|
| Dedicated memory store | Not implemented |
| Memory runtime APIs | Not implemented |
| Plugin memory contributions | Not implemented |
| Retrieval / indexing / embeddings for memory | Not implemented |

**What exists today (related but not memory):**

| Mechanism | Role |
|-----------|------|
| `state.toml` + `transitions.jsonl` | Authoritative project state and transition history (`006_STATE_MACHINE.md`) |
| `workflow-progress.json` | Workflow and task progress persistence |
| Artifacts on disk | Plugin-scaffolded paths; lifecycle tracked in orchestration (`008_ARTIFACTS.md`) |
| Event bus | In-process, non-persistent coordination telemetry (`003_RUNTIME.md`) |
| Skill metadata | Registered via plugins; no execution or storage layer (`011_SKILLS.md`) |

These mechanisms provide **explicit, file-backed orchestration state**. They do not constitute a memory system for AI context, semantic recall, or cross-session knowledge graphs.

---

## Why deferred

Per [`ARCHITECTURE_REVIEW_V0.5.md`](../docs/ARCHITECTURE_REVIEW_V0.5.md):

- Memory system design should follow **AI workers producing retrievable context** (implemented in M13, expanded in M16).
- Designing memory before worker execution binding would invent runtime behavior without an implementation anchor.

---

## Prerequisites before design

1. **AI worker binding** — workers invoke `AIService` with durable task outcomes (`017_AI_PROVIDERS.md`, implemented in M13).
2. **Artifact provenance** — clearer rules for what content workers produce and where it lives (`008_ARTIFACTS.md`).
3. **Security model** — memory implies retention of potentially sensitive data (`013_SECURITY.md`, M14 baseline complete).

---

## Relationship to other documents

| Document | Relationship |
|----------|--------------|
| `000_VISION.md` | Lists memory as a long-term Vedaws responsibility |
| `001_PHILOSOPHY.md` | State must be explicit; implicit conversation memory is an anti-pattern |
| `002_CORE.md` | Project, State, Artifacts — orchestration vocabulary; no Memory core concept yet |
| `011_SKILLS.md` | Skill metadata is not memory |
| `017_AI_PROVIDERS.md` | AI routing exists; no memory-backed context injection |
| `015_ROADMAP.md` | Schedules memory work after M13–M16 foundations |

---

## Future direction (not specified at v0.5)

When memory is designed, it should:

- Remain **project-scoped** under `.vedaws/` or an explicitly documented extension path
- Not replace `state.toml` as authoritative operational state
- Integrate with workers and AI providers at the plugin edge where possible
- Produce auditable, attributable records consistent with `001_PHILOSOPHY.md`

Detailed memory architecture (stores, schemas, retention, retrieval APIs) is **out of scope** until the prerequisites above are met.

---

## TODO

- Define memory architecture after M13 (AI worker binding) delivers retrievable execution context
- Align with `013_SECURITY.md` retention and trust boundaries
- Update `002_CORE.md` only if Memory becomes a canonical core concept (requires architecture review)
