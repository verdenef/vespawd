# Skills

**Version:** 0.5.0

**Status:** Active — M16 baseline (metadata + runtime consumer binding)

## Purpose

**Skills** describe specialized capability knowledge that workers may apply during task execution. The runtime registers skill metadata from plugins and makes those skills available to worker implementations at execution time.

---

## Registration

Plugins contribute skills via the SDK:

```python
context.contribute_skill("software.architecture", "Architecture", "System structure...")
```

Skills appear in `vedaws plugins info <plugin-id>` under Contributions.

---

## M16 architecture boundary

| Surface | Status |
|---------|----------------|
| `contribute_skill()` SDK | **Frozen** — registration API remains |
| Skill metadata in plugin contributions | **Implemented** — id, name, description |
| Skill resolution during worker `execute()` | **Implemented** (first consumer: `AIExecutableWorker`) |
| Skill discovery CLI | **Not implemented** |
| Workflow task `skills` / `skill` metadata | **Implemented** for worker guidance |

Contributing a skill registers metadata that can be resolved by workers at execution time. Skills remain a worker-facing execution aid, not an orchestration primitive. The runtime and dispatcher remain capability-driven.

---

## Software Workflow Plugin Skills

| Skill id | Name | Description |
|----------|------|-------------|
| `software.scoping` | Software scoping | Goals, constraints, success criteria |
| `software.architecture` | Architecture | System structure and boundaries |
| `software.api-design` | API design | Interface contracts |
| `software.implementation` | Implementation | Build to specification |
| `software.testing` | Testing | Verification and QA |
| `software.review` | Code review | Pre-handoff review |
| `software.handoff` | Handoff | Operational packaging |

---

## Unity Game Development Plugin Skills

| Skill id | Name | Description |
|----------|------|-------------|
| `unity-csharp` | Unity C# | C# scripting patterns for Unity projects |
| `unity-prefabs` | Unity prefabs | Prefab composition and reuse |
| `unity-ui` | Unity UI | uGUI / UI Toolkit interface design |
| `unity-animation` | Unity animation | Animation clips, timelines, and state machines |
| `unity-ai` | Unity AI | NPC behaviour and navigation placeholders |
| `unity-performance` | Unity performance | Profiling and optimization practices |

---

## Runtime consumption (M16)

`AIExecutableWorker` is the first concrete runtime consumer of skill metadata:

- skills are resolved during worker execution from plugin contributions
- task-declared skills contribute prompt guidance and execution context
- capability-based worker dispatch is unchanged
- skills remain independent of AI and may be consumed by non-AI workers in later milestones

---

## Relationship to Other Documents

| Document | Relationship |
|----------|--------------|
| `010_PLUGINS.md` | `contribute_skill` SDK |
| `004_WORKERS.md` | Workers may consume skills during execution |
| `017_AI_PROVIDERS.md` | AI routing remains provider-neutral while workers consume skills |
| `016_IMPLEMENTATION_PLAN.md` | M16 skills & config milestone |

---

## TODO

- Skill discovery CLI — deferred
- Non-AI worker skill consumers — future expansion
- Skill validation linting for orphaned task skill ids — future expansion
