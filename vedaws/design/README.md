# Vedaws Architecture Index

**Architecture version:** 0.5.0 (frozen at Milestone 12)  
**Freeze declaration:** [`docs/ARCHITECTURE_FREEZE_V0.5.md`](../docs/ARCHITECTURE_FREEZE_V0.5.md)  
**Public API contract:** [`docs/API_STABILITY.md`](../docs/API_STABILITY.md)  
**Architecture review:** [`docs/ARCHITECTURE_REVIEW_V0.5.md`](../docs/ARCHITECTURE_REVIEW_V0.5.md)

This directory contains the canonical architecture of Vedaws.

Every design document describes a fundamental concept of the system.

## Rules

1. These documents are the architectural source of truth.
2. Implementation should follow the architecture.
3. If implementation intentionally changes the architecture, update the corresponding design document in the same milestone.
4. Do not create duplicate architectural concepts.
5. Extend existing concepts before introducing new ones.
6. Design documents describe *what Vedaws is*, not merely its current implementation.
7. All future contributors (human or AI) should consult this directory before making architectural changes.
8. Post-M12 changes must respect the v0.5 freeze unless an architecture review approves otherwise.

---

# Architecture Map

| Document | Purpose | Status |
| -------- | ------- | ------ |
| `000_VISION.md` | Long-term vision and purpose of Vedaws | Stable |
| `001_PHILOSOPHY.md` | Core principles and design philosophy | Stable |
| `002_CORE.md` | Fundamental concepts and terminology | Active |
| `003_RUNTIME.md` | Runtime architecture and orchestration | Active |
| `004_WORKERS.md` | Worker model and execution abstraction | Active |
| `005_AUTOMATION.md` | Automation architecture | Active |
| `006_STATE_MACHINE.md` | Project lifecycle and state transitions | Active |
| `007_PROJECT_MODEL.md` | Project structure and lifecycle | Active |
| `008_ARTIFACTS.md` | Artifacts produced and consumed by Vedaws | Active |
| `009_MEMORY.md` | Persistent memory architecture | Deferred — out of v0.5 scope |
| `010_PLUGINS.md` | Plugin architecture and extension model | Active |
| `011_SKILLS.md` | Skill abstraction and execution guidance model | Active |
| `012_CONFIGURATION.md` | Configuration hierarchy and loading | Active |
| `013_SECURITY.md` | Security boundaries and trust model | Active (M14 baseline) |
| `014_REPOSITORY.md` | Vedaws monorepo layout | Active |
| `015_ROADMAP.md` | Architectural roadmap (M13+ toward v1) | Living |
| `016_IMPLEMENTATION_PLAN.md` | Implementation strategy and milestone gates | Living |
| `017_AI_PROVIDERS.md` | AI provider SDK and capability routing | Active |
| `018_AI_WORKERS.md` | AI worker execution binding and runtime integration | Active |

Individual document headers may carry finer-grained version labels; the **architecture baseline** for this index is **0.5.0**.

---

# Architecture Freeze (v0.5)

Architecture v0.5 is **declared frozen** after Milestone 12. The orchestration spine (runtime, plugins, events, automation, AI routing) and extension model are the authoritative baseline.

| Artifact | Role |
| -------- | ---- |
| [`docs/ARCHITECTURE_FREEZE_V0.5.md`](../docs/ARCHITECTURE_FREEZE_V0.5.md) | What is frozen, deferred, and how to request changes |
| [`docs/API_STABILITY.md`](../docs/API_STABILITY.md) | Frozen public APIs and unstable surfaces |
| [`docs/ARCHITECTURE_REVIEW_V0.5.md`](../docs/ARCHITECTURE_REVIEW_V0.5.md) | Audit source (7.8/10 architecture; not v1-ready) |
| `015_ROADMAP.md` | M13–M16 completion and post-freeze v1 priorities |
| `016_IMPLEMENTATION_PLAN.md` | Milestone deliverables and test expectations |

Before changing frozen decisions, consult [`.ai/architect_escalation.md`](../.ai/architect_escalation.md).

---

# Architecture Layers (implemented)

```
CLI → RuntimeContext → EventBus (in-process, synchronous)
  ↓
AutomationEngine → rules (on_event → if → then)
  ↓
AIService → AIProviderRegistry (capability routing)
  ↓
PluginPlatform → PluginContributions (workers, commands, templates, skills, events, automation, ai_providers)
  ↓
Project templates → vedaws init --template (software, unity, …)
  ↓
Plugin CLI dispatch (plugin_commands.py) → plugin handlers
  ↓
WorkerDispatcher → publishes/consumes worker events
  ↓
WorkflowEngine (includes TaskRegistry) → publishes workflow/task events
  ↓
StateEngine → publishes ProjectStateChanged
  ↓
WorkerRegistry → Workers (ExecutableWorker | ManifestWorker)
```

**Bootstrap order:** config → logging → EventBus → workers → PluginPlatform → project detection → WorkerDispatcher → AIService → AutomationEngine → `RuntimeContext`.

Future layers (not yet implemented):

```
Vendor AI plugins (Gemini, OpenAI, …)
    ↓
External Tools / MCP adapters (plugin-local)
```

Deferred:

```
Memory system (009_MEMORY.md)
    ↓
Scheduling / background automation
    ↓
Distributed execution
```

---

# Documentation Lifecycle

Each document progresses through one of these stages:

| Stage | Meaning |
| ----- | ------- |
| **Stable** | Mature reference; rare changes (vision, philosophy). |
| **Active** | Implemented architecture; evolves with milestones. |
| **Living** | Continuously updated roadmaps and plans (`015`, `016`). |
| **Draft** | Partial specification or known gaps documented in milestone design proposals. |
| **Deferred** | Intentionally out of v0.5 scope; no runtime implementation (`009_MEMORY.md`). |
| **Frozen (v0.5)** | Implemented baseline locked per `ARCHITECTURE_FREEZE_V0.5.md`; subset of Active docs at freeze time. |

---

# Contributor Guidelines

Before implementing a new feature:

1. Check whether an existing design document already defines the concept.
2. If yes, update that document instead of creating a new one.
3. If no suitable document exists, discuss the architecture before introducing a new concept.
4. Keep implementation and architecture synchronized.
5. Read `docs/API_STABILITY.md` before changing public contracts.
6. Do not add domain logic to `runtime/vedaws/` — use plugins (`010_PLUGINS.md`).

Repository layout: `014_REPOSITORY.md`.

---

# Design Philosophy

The implementation may evolve.

The architecture should remain intentional.

Every new feature should strengthen the architecture rather than bypass it.
