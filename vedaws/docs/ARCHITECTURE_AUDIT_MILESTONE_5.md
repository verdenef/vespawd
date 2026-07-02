# Architecture Audit — Post Milestone 5

**Date:** 2026-06-30  
**Scope:** All documents in `design/`, full runtime implementation through Sprint 5 (Worker Execution Engine)  
**Audience:** Pre–Milestone 6 planning, open-source v1 readiness review  
**Method:** Design-doc cross-read, implementation inspection, sprint deliverable review. No code changes.

---

## 1. Current Architecture Overview

Vedaws is a Python CLI-first DevOS with a layered orchestration stack:

```
CLI (vedaws)
  → Runtime bootstrap (config, logging, discovery)
  → RuntimeContext (plugins, workers, project, dispatcher)
  → Project detection (.vedaws/project.toml)
  → StateEngine (canonical project state, transitions.jsonl)
  → WorkflowEngine (definitions, task registry, progress)
  → WorkerDispatcher (capability match, lifecycle, execute)
  → ExecutableWorker (mock implementations today)
```

**What exists and works end-to-end**

| Layer | Implementation | Persistence |
|-------|----------------|-------------|
| Project init | `project/init.py` | `.vedaws/project.toml`, `config.toml` |
| Project state | `project/state/` | `state.toml`, `transitions.jsonl` |
| Workflows & tasks | `workflow/` | `workflows/*.workflow.toml`, `workflow-progress.json` |
| Worker registry | `workers/` + bundled `workers/` manifests | In-memory per session |
| Dispatch & run | `dispatch/` | Outcomes folded into workflow progress |
| Plugins | `plugins/` discovery only | None |
| Health | `doctor/` | N/A |

**Milestone progression (Sprints 1–5)**

1. Runtime skeleton, config, plugin discovery  
2. Worker registry (manifest-only workers)  
3. Project lifecycle state machine  
4. Workflow & task modeling (no execution)  
5. Worker dispatch with mock executors (`vedaws run`)

The system can initialize a project, activate a default workflow, dispatch ready tasks to `mock.success`, and reconcile workflow progress with project state. This is a credible **orchestration prototype**, not yet a product-grade DevOS.

**Design corpus status**

| Category | Documents | Maturity |
|----------|-----------|----------|
| Vision / philosophy / core | 000–002 | Substantive, stable intent |
| Runtime / workers / state | 003–004, 006 | Substantive; partially implemented |
| Automation, artifacts, memory, plugins, skills, config, security, repo | 005, 007–014 | Empty stubs (TODO only) |
| Roadmap / implementation plan | 015–016 | Empty stubs |

Roughly **41% of indexed design documents are unwritten**. Implementation has outpaced documentation for several concepts while lagging far behind the architectural ambition in others.

---

## 2. Strengths

### Clear philosophical north star

`000_VISION.md`, `001_PHILOSOPHY.md`, and `002_CORE.md` articulate a coherent mission: explicit state, coordination vs execution separation, human authority, domain neutrality, and worker replaceability. This gives Milestone 6+ a principled decision framework.

### Layered package structure

`runtime/vedaws/` is organized by concern (`project/`, `workflow/`, `dispatch/`, `workers/`, `config/`, `cli/`). Boundaries are recognizable and testable. Forty-six automated tests cover bootstrap, CLI, state, workflow, dispatch, workers, and plugins.

### State machine is explicit and persisted

`StateEngine` with `VALID_TRANSITIONS`, append-only `transitions.jsonl`, and trigger categories (`human_decision`, `task_outcome`, `workflow_rule`, `system`) matches the legibility goals in design. `006_STATE_MACHINE.md` was updated (v0.2.0) to reflect Sprint 3 implementation — a good precedent for design/implementation sync.

### Workflow and task model is practical

TOML workflow definitions, dependency evaluation, derived workflow status, and task lifecycle enums align with `002_CORE.md`. The default three-task workflow exercises the full path from activation through dispatch to completion.

### Worker contract is extensible

`ExecutableWorker`, `TaskDispatch`, and `TaskOutcome` provide a minimal but correct execution boundary. Mock workers prove the dispatch loop without coupling to AI vendors — appropriate for architecture validation.

### Configuration layering works

User → project → environment override pattern in `config/loader.py` is sound and matches expected DevOps conventions.

### Doctor command provides operational visibility

Health checks for configuration, runtime, plugins, workers, state, workflows, dispatcher, and execution pipeline give early operators a single diagnostic entry point.

---

## 3. Weaknesses

### Massive design–implementation gap

Ten core design areas (automation, artifacts, memory, plugins, skills, configuration spec, security, repository model, roadmap, implementation plan) have **no architectural content**. Contributors cannot rely on `design/` alone to extend the system safely.

### Orchestration is CLI-driven and synchronous

`vedaws run` is a blocking, single-threaded loop. There is no background runtime, event bus, scheduler, or long-running daemon despite `003_RUNTIME.md` describing Active/Waiting lifecycle phases and `design/README.md` listing Event Bus as a future layer.

### Dispatch ignores project-state eligibility

`006_STATE_MACHINE.md` defines when dispatch is allowed (e.g. **Executing** only). The dispatcher never checks `ProjectState` or `allows_orchestration`. Tasks can be dispatched while the project is in **Ready**, **Planning**, or potentially inappropriate states if the CLI is used.

### Dual bypass paths undermine the execution model

`vedaws tasks complete` and `vedaws tasks fail` record outcomes without workers, without `DISPATCHED`/`RUNNING` transitions, and without approval gates. This is useful for testing but violates the Sprint 5 execution contract and design invariants if left available in production.

### No audit trail for dispatches

Design requires traceable coordination events (`003_RUNTIME.md` § Coordination Audit Trail). Implementation records task `outcome_message` and state transitions but not: who was dispatched, when, with what dispatch package, or worker diagnostics.

### Plugin system is decorative

Plugins are discovered and listed. They do not register workers, workflows, state extensions, or hooks. `hello` plugin is a placeholder. Per-project plugin activation described in design does not exist.

### Artifact, skill, and automation concepts are zero

Despite being core concepts in `002_CORE.md`, none are modeled, persisted, or referenced in dispatch packages beyond empty fields.

### Manifest workers mislead operators

Eight bundled workers (human, AI, tool) appear healthy in `vedaws workers` but cannot execute. Doctor reports worker registry success while execution pipeline may warn about capability gaps — confusing UX for open-source users.

### Open-source release blockers

`pyproject.toml` declares **Proprietary** license. No CONTRIBUTING, no plugin SDK docs, no versioning policy, no migration story for `.vedaws/` format changes.

---

## 4. Architectural Inconsistencies

### 4.1 Project lifecycle: `002_CORE.md` vs `006_STATE_MACHINE.md`

| Source | Project phases |
|--------|----------------|
| `002_CORE.md` | Created → Initialized → **Active** → Paused → Completed → Archived |
| `006_STATE_MACHINE.md` (implemented) | Created → Initialized → Planning → Ready → Executing → … (11 operational states) |

**Active** and **Paused** from core concepts do not exist in the implemented state machine. `006` explicitly notes reconciliation with `002` is TODO. This is the single largest terminology conflict in the architecture.

### 4.2 `design/README.md` layer diagram vs code

The README shows separate **Task Engine** and **Workflow Engine** layers. Implementation folds tasks into `workflow/` (registry inside `WorkflowEngine`). No independent task engine module exists. The diagram also places Dispatcher above Workflow Engine; code wires `WorkerDispatcher` to `WorkflowEngine` directly with no mediating runtime orchestration service.

### 4.3 Dispatch eligibility table vs runtime behavior

`006_STATE_MACHINE.md` § Orchestration Eligibility:

- **Ready** → Dispatch: **No**
- **Executing** → Dispatch: **Yes**

Implementation dispatches whenever a task is `ready`, regardless of project state. `allows_orchestration` exists on `ProjectState` but is **never enforced** (noted as future work in `SPRINT_3_SUMMARY.md`).

### 4.4 Worker lifecycle: design vs `WorkerStatus`

`004_WORKERS.md` per-task lifecycle: Available → Assigned → Executing → **Returning** → **Released**.

Implementation adds `ASSIGNED` and `EXECUTING` to `WorkerStatus` but skips Returning/Released; workers jump back to `AVAILABLE` in a `finally` block. Worker-level Completed/Failed from `002_CORE.md` are absent.

### 4.5 Capability model: task vs worker

Tasks use a single string `capability` (maps to `work_type` only). Workers declare `work_type` + `scope`. Matching ignores scope entirely in `matcher.py`. Design (`004_WORKERS.md`) treats scope as a first-class dispatch dimension.

### 4.6 Duplicate worker identity paths

Mock workers exist as:

1. Python classes in `runtime/vedaws/workers/mock/`  
2. TOML manifests in `workers/mock/`  
3. Programmatic registration in `bootstrap.register_mock_workers()`

Discovery loads manifests as non-executable `ManifestWorker`; bootstrap then overwrites with `ExecutableWorker`. The manifests are documentation-only in practice — an confusing dual source of truth.

### 4.7 State sync: two mechanisms, uneven bridge support

- `_try_state_transition()` uses `_transition_bridge()` for indirect paths (e.g. Ready → Executing → Failed).  
- `_sync_project_state()` only attempts **direct** transitions.

Workflow-driven reconciliation can fail silently when a bridge is required, leaving project state stale while workflow progress advances.

### 4.8 `project.toml` state mirror

`state.toml` is authoritative; `project.toml` state field is synced best-effort via string replacement in `sync_manifest_state()`. Two sources of truth for humans; risk of drift if files are edited manually.

### 4.9 Human approval gates

`requires_approval` on tasks transitions to `awaiting_approval` on success — but only via outcome recording. Nothing blocks dispatch or manual `tasks complete` before approval. Gates are recorded after the fact, not enforced before effect propagation.

### 4.10 AI worker manifests vs default workflow

Placeholder AI workers declare capabilities like `code-generation`, `analysis`. Default workflow tasks require `planning`, `validation`, `review`. No documentation explains capability naming conventions or how domains map.

---

## 5. Technical Debt

| Item | Severity | Notes |
|------|----------|-------|
| `allows_orchestration` unused | High | Documented API, zero enforcement |
| `tasks complete/fail` bypass | High | Undermines execution lifecycle |
| `_sync_project_state` no bridges | High | State/workflow desync risk |
| Hardcoded `mock.success` preference in `matcher.py` | Medium | Violates replaceability; test-only logic in production path |
| `ManifestWorker` stale docstring ("Sprint 2, no execution") | Low | Misleading for contributors |
| `StateEngine.subscribe()` unused | Medium | Event bus planned but not started |
| String-based `project.toml` state sync | Medium | Fragile; should regenerate or use TOML library |
| No workflow cycle detection | Medium | Invalid graphs accepted at load time |
| No concurrency controls | Medium | `run_until_idle` dispatches sequentially; design allows parallel |
| No timeout/cancellation | Medium | Worker failures only via mock outcome or exception |
| Broad `except Exception` in dispatcher/doctor | Low | Acceptable for CLI; needs tightening for library use |
| Duplicate mock worker registration path | Low | Confusing bootstrap order |
| 46 tests, no integration test for full CLI golden path in CI docs | Low | Coverage is unit-heavy |
| Empty scaffold dirs (`automation/`, `skills/`, `templates/`) | Low | Noise for OSS visitors |

---

## 6. Missing Concepts

Relative to `002_CORE.md` and downstream design intent:

| Concept | Design status | Implementation status |
|---------|---------------|----------------------|
| **Automation** | Core concept | Not started |
| **Artifacts** | Core concept | Not started |
| **Skills** | Core concept | Not started |
| **Memory** | Indexed, stub | Not started |
| **Plugin activation (per project)** | Specified in 003, 002 | Not started |
| **Event bus** | README future layer | Not started |
| **Dispatch audit log** | Required by 003 | Not started |
| **Task cancellation** | Lifecycle in 002 | Not started |
| **Partial / escalation outcomes** | 004 outcome categories | Only success/failure used |
| **Worker timeout & monitoring** | 003, 004 | Not started |
| **Concurrent dispatch** | 003 | Not started |
| **Project pause/resume** | 002 lifecycle | No **Paused** state |
| **Configuration spec** | 012 stub | Ad hoc schema only |
| **Security model** | 013 stub | No boundaries, secrets, or sandbox |
| **Repository / monorepo model** | 014 stub | Not started |
| **Rich dispatch package** | 004 (artifacts, skills, constraints) | `TaskDispatch` is minimal |
| **Plugin-provided workflows** | 002, 010 | Not started |
| **Runtime Waiting/Stopping phases** | 002, 003 | Only `RuntimeStatus` enum partially used |

---

## 7. Suggested Refactors (Low Priority)

1. **Consolidate mock worker definitions** — single source: either code registry or manifests with a `runtime = "vedaws.mock"` loader, not both.  
2. **Extract `TaskService` from `WorkflowEngine`** — align with README layer diagram without big-bang rewrite; clarify task vs workflow responsibilities.  
3. **Replace string mutation in `sync_manifest_state`** with TOML round-trip or drop mirrored state from `project.toml`.  
4. **Unify reporter modules** — `status/`, `workers/reporter`, `workflow/reporter`, `dispatch/reporter` could share formatting helpers.  
5. **Mark manifest-only workers explicitly** in CLI (`EXEC: manifest-only`) instead of generic `no`.  
6. **Populate or remove empty scaffold directories** (`automation/`, `skills/`, `templates/`) before OSS launch.  
7. **Wire `StateEngine.subscribe()`** to a lightweight in-process event log as stepping stone to event bus.  
8. **Validate workflow DAG** at load time (cycle detection, unknown `depends_on` refs).

---

## 8. Suggested Refactors (High Priority)

1. **Reconcile `002_CORE.md` and `006_STATE_MACHINE.md`** — pick one project lifecycle vocabulary; update the other in Milestone 6 planning. Until then, all new code should treat `006` as authoritative.  
2. **Enforce orchestration eligibility** — dispatcher and `run_until_idle` must check `ProjectState.allows_orchestration` and dispatch-specific rules from `006`.  
3. **Unify state transition paths** — `_sync_project_state` should use the same bridge logic as `_try_state_transition`, or delegate to a single `StateTransitionService`.  
4. **Gate or deprecate `tasks complete/fail`** — restrict to dev mode, require `RUNNING` status, or route through dispatcher for consistency.  
5. **Introduce dispatch audit persistence** — append-only `dispatches.jsonl` with worker id, task ref, timestamps, outcome, correlation id. Required for legibility and OSS trust.  
6. **Define worker loading protocol** — manifest field (e.g. `executor = "module:Class"`) so AI/tool workers become executable without hardcoded `register_mock_workers()`.  
7. **Document and implement capability naming convention** — bridge task `capability` to worker `work_type`/`scope`; include scope in matching.  
8. **Author `010_PLUGINS.md` and `012_CONFIGURATION.md`** before expanding plugin or config surface — highest-impact missing specs.  
9. **Approval gate enforcement** — block effect propagation (and optionally dispatch) until approval recorded when `requires_approval = true`.  
10. **Clarify runtime entry point** — introduce an `Orchestrator` or `RuntimeSession` object that owns bootstrap, dispatch, and shutdown instead of growing `commands.py` and `bootstrap.py` ad hoc.

---

## 9. Scalability Concerns

### Execution model

All worker execution is **in-process and synchronous**. AI providers will need async I/O, streaming, timeouts, and cancellation. The current `ExecutableWorker.execute()` signature will not scale to network-bound workers without an execution substrate (thread pool, asyncio, or worker process isolation).

### Concurrency

`run_until_idle` processes one task at a time. Independent tasks in parallel workflows cannot run concurrently. At scale, this becomes a throughput bottleneck.

### Persistence

JSON and JSONL files in `.vedaws/` are fine for single-user CLI prototypes. Multi-project, multi-user, or CI-heavy usage will need:

- File locking or database backend  
- Schema versioning and migrations  
- Conflict resolution for concurrent writers  

### Worker registry

In-memory registry rebuilt every bootstrap. No persistent worker availability, health history, or distributed worker pools.

### State reconciliation

Derived project state from workflow progress (`_derive_project_state`) is heuristic. Multiple active workflows, partial failures, and recovery paths will produce edge cases not covered by tests.

### Discovery

Linear scan of search paths and `rglob` for manifests. Acceptable now; needs indexing/caching for large installations.

### Observability

Logging is basic. No structured logs, metrics, or tracing hooks for dispatch latency, queue depth, or failure rates.

---

## 10. Plugin Readiness Assessment

| Criterion | Ready? | Evidence |
|-----------|--------|----------|
| Discovery | Partial | `plugins/discovery.py` finds `vedaws.plugin.toml` |
| Registry | Partial | `PluginRegistry` stores manifests only |
| Per-project activation | No | No activation state in `.vedaws/` |
| Worker registration via plugin | No | Workers discovered from filesystem only |
| Workflow registration via plugin | No | Workflows loaded from `.vedaws/workflows/` only |
| State extensions | No | No plugin state dimensions |
| Lifecycle hooks | No | No load/activate/deactivate API |
| Conflict detection | No | Duplicate IDs skipped with warning only |
| SDK / loader contract | No | `010_PLUGINS.md` is empty |
| Isolation / sandbox | No | `013_SECURITY.md` is empty |

**Verdict:** Plugin architecture is **~15% ready**. Discovery proves the concept; everything that makes plugins valuable for domain neutrality is unbuilt. Milestone 6 should not assume plugin-driven extensibility without first authoring `010_PLUGINS.md` and a minimal activation model.

---

## 11. AI Provider Readiness Assessment

| Criterion | Ready? | Evidence |
|-----------|--------|----------|
| Execution boundary (`ExecutableWorker`) | Yes | `workers/interface.py`, `execution.py` |
| Dispatch package | Minimal | No prompts, model config, token limits, or conversation context |
| Outcome taxonomy | Partial | `TaskOutcomeStatus` has partial/escalation; unused |
| Provider adapters | No | `ai.claude`, `ai.chatgpt`, `ai.gemini` are manifest placeholders |
| Secrets / API keys | No | No config or security model |
| Async / streaming | No | Synchronous `execute()` only |
| Non-determinism handling | No | Design requires visibility; not implemented |
| Human review of AI output | Partial | `requires_approval` flag exists; not enforced pre-effect |
| Capability alignment | No | AI manifests use different work_types than workflows |
| Rate limiting / retries | No | Not in dispatcher |
| Cost / usage tracking | No | Not started |
| Test doubles | Yes | Mock workers validate orchestration |

**Verdict:** AI readiness is **~25% for orchestration plumbing**, **~5% for real provider integration**. The Sprint 5 mock layer is the correct architectural step. Milestone 6+ needs:

1. A `ProviderWorker` base or adapter interface (auth, execute, health)  
2. Async execution model  
3. `012_CONFIGURATION.md` + `013_SECURITY.md` for API keys  
4. Capability vocabulary alignment  
5. Review queue for AI outcomes before state propagation  

Do not integrate Gemini, ChatGPT, Claude, or Cursor until items 1–3 exist — otherwise each provider will embed one-off logic in the dispatcher path.

---

## 12. Overall Architecture Score

### **5.5 / 10** (preparing for open-source v1)

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Vision & principles | 9/10 | Exceptional clarity in 000–001 |
| Core concept model | 8/10 | 002 is thorough; conflicts with implementation |
| Design corpus completeness | 4/10 | Majority of indexed docs are empty |
| Implementation coherence | 6/10 | Clean packages; eligibility and bypass gaps |
| Design–implementation alignment | 5/10 | State machine updated; core lifecycle stale |
| Extensibility (plugins/workers) | 4/10 | Contracts started; activation missing |
| Production readiness | 3/10 | Sync CLI, file persistence, no security |
| Testability | 7/10 | Good unit coverage for sprint scope |
| Legibility & auditability | 5/10 | State history yes; dispatch audit no |
| OSS release readiness | 3/10 | License, docs gaps, misleading worker list |

**Summary judgment:** Vedaws has a **strong architectural intent** and a **working vertical slice** (init → workflow → dispatch → state). It is an excellent **internal prototype** and a credible foundation for Milestone 6. It is **not** ready for open-source v1 without resolving lifecycle terminology, enforcement gaps, missing design specs, dispatch auditability, and the plugin/AI loader story.

**Recommended Milestone 6 focus (architecture, not implementation prescription):**

1. Author `007_PROJECT_MODEL.md`, `010_PLUGINS.md`, `012_CONFIGURATION.md`  
2. Reconcile `002` ↔ `006` project lifecycle  
3. Enforce orchestration eligibility and approval gates  
4. Define executable worker loading from manifests  
5. Add dispatch audit persistence  
6. Decide sync vs async execution substrate for AI Milestone 7+

---

*This audit is descriptive, not normative. It does not authorize design changes. Per `.cursor/rules/architecture.md`, inconsistencies should be resolved through explicit design updates before implementation proceeds.*
