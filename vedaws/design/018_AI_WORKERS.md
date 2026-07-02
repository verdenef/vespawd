# AI Workers

**Version:** 0.5.0

**Status:** Active — implemented in M13, extended in M16

## Purpose

This document specifies how **AI workers** bind the existing **AI Provider SDK** (Milestone 12) into the **Worker System** without changing the v0.5 orchestration freeze.

An AI worker is an `ExecutableWorker` whose `execute()` implementation requests a **capability** through `AIService`. Provider selection, fallback chains, and vendor isolation remain in `AIProviderRouter` and plugin-owned `AIProvider` implementations — not in workflow definitions or the dispatcher.

**Objective (M13):** Close the gap documented in `017_AI_PROVIDERS.md` by enabling workflow-dispatched AI workers to invoke `AIService` during execution.

---

## Architectural position

```
WorkflowEngine          WorkerDispatcher          ExecutableWorker
     │                         │                         │
     │  task.capability        │  TaskDispatch           │
     └────────────────────────►│────────────────────────►│
                               │                         │
                               │              AIExecutableWorker (M13)
                               │                         │
                               │                         ▼
                               │                    AIService
                               │                         │
                               │                         ▼
                               │               AIProviderRouter
                               │                         │
                               │                         ▼
                               │                  AIProvider (plugin)
```

| Layer | Responsibility | M13 change |
|-------|--------------|------------|
| Workflow | Declares tasks and `capability` strings | Additive `ai_capability` and `skills` metadata supported |
| `WorkerDispatcher` | Capability match, `TaskDispatch`, outcome recording | `AIService` and skill catalog binding without dispatch redesign |
| `ExecutableWorker` | Bounded execution, `TaskOutcome` | `AIExecutableWorker` remains additive; existing workers unchanged |
| `AIService` | Capability requests (`chat`, `generate`, …) | **No API change** |
| `AIProviderRouter` | Config-driven provider selection | **No change** |
| Provider plugins | Vendor-neutral `AIProvider` | `mock-ai` adds executable workers |

Workers remain the **execution boundary**. Workflows still dispatch workers. Automation still uses `execute_worker`. The runtime remains vendor-neutral.

---

## Integration with frozen types

### `Worker` / `ExecutableWorker`

No change to the ABC contracts in `vedaws.workers.interface`:

- `execute(self, dispatch: TaskDispatch) -> TaskOutcome` — **frozen signature**
- `health_check()`, `metadata`, lifecycle status — unchanged

M13 introduces a **core** abstract base class:

| Type | Package | Role |
|------|-------------------|------|
| `AIExecutableWorker` | `vedaws.workers.ai_worker` | Holds `AIService`; implements shared AI request/response mapping |
| Domain / demo subclasses | Plugin packages | Prompt templates, artifact side effects |

`AIExecutableWorker` is domain-neutral. It does not embed software, Unity, or Git semantics.

`WorkerType.AI` already exists in `vedaws.workers.types` — AI workers set `worker_type=WorkerType.AI`.

### `TaskDispatch` / `TaskOutcome`

**Frozen fields** (per `API_STABILITY.md`): `workflow_id`, `task_id`, `task`, `project_name`, `instructions`.

M13 does **not** add fields to `TaskDispatch`. AI-specific inputs are derived at execution time from:

| Source | Use |
|--------|-----|
| `dispatch.task.description` | Primary task intent |
| `dispatch.task.name` | Short label |
| `dispatch.instructions` | Worker-specific directives (e.g. project root path) |
| `dispatch.task.capability` | Dispatch matching **and** default AI capability (see routing) |
| `TaskOutcome.data` | AI metadata (`provider_id`, `model`, `ai_capability`, `content`, …) |

`TaskOutcomeStatus` values remain **frozen**: `success`, `failure`, `partial`, `escalation`.

### `WorkerDispatcher`

**Frozen public API:** `dispatch_and_execute()`, `list_ready_tasks()`, `find_worker_for_task()`, `DispatchResult`, `DispatchStatus`.

M13 changes to the dispatcher:

| Change | Allowed? | Description |
|--------|----------|-------------|
| Constructor `ai_service` parameter | Yes (additive) | Optional reference for late-bound workers |
| Logic before `worker.execute()` | Yes (internal) | Ensure `AIExecutableWorker` has service wired |
| Async / job queue | **No** | Deferred post-M15 |
| Direct `AIService` calls | **No** | Dispatcher does not bypass workers |

Capability matching (`dispatch/matcher.py`) is **unchanged**: `task.capability` equals `WorkerCapability.work_type`.

### `AIService` / `AIProviderRouter`

**Frozen** (per `017_AI_PROVIDERS.md`, `API_STABILITY.md`):

- `chat()`, `generate()`, `resolve_provider()`, `resolve_chain()`, `provider_health()`
- `[ai]` / `[ai.capabilities.*]` configuration shape
- No vendor imports in `runtime/vedaws/`

M13 workers call existing methods only. Provider selection is **never** performed in worker plugins by vendor id — only by **capability string** passed into `AIService`.

**Retry at router level (M13):** `AIExecutableWorker` may call `resolve_chain(ai_capability)` and attempt providers **sequentially** until one returns a response or all fail. This uses existing router/registry behavior; it does not add new config keys.

---

## Capability routing

Two distinct routing steps must not be conflated:

### 1. Dispatch routing (worker selection)

Unchanged from v0.5:

```
workflow [[tasks]].capability  ==  worker.metadata.capabilities[].work_type
```

Examples today:

| Workflow capability | Worker | Plugin |
|--------------------|--------|--------|
| `software-implementation` | `software.implementation` | software |
| `git-status` | `git.status` | git |
| `implement` (M13 demo) | `mock-ai.implement` | mock-ai |

### 2. AI provider routing (capability request)

After a worker is selected, `AIExecutableWorker` maps the task to a **standard AI capability** for `AIService`:

| Standard AI capability | Constant / `STANDARD_AI_CAPABILITIES` |
|------------------------|--------------------------------------|
| `chat`, `plan`, `implement`, `review`, `summarize`, `document`, `refactor`, `explain` | `vedaws.ai.capabilities` |

**Resolution order** for the AI capability string:

1. Optional workflow field `ai_capability` on the task (additive TOML — see below) if present and valid
2. Else if `task.capability` is a member of `STANDARD_AI_CAPABILITIES` → use it directly
3. Else if the worker declares an `ai_capability` override on the worker class (worker metadata extension, not dispatch match key) → use override
4. Else → `TaskOutcome.failure` with message explaining missing AI capability mapping

This allows:

- **M13 demo workflows** — `capability = "implement"` matches `mock-ai` workers directly
- **Existing domain workflows** — keep `software-implementation` for dispatch; set `ai_capability = "implement"` on the task when migrating a task to AI execution

### Additive workflow TOML (M13)

```toml
[[tasks]]
id = "implement"
name = "Implement"
capability = "software-implementation"   # dispatch match (unchanged)
ai_capability = "implement"              # optional — AI request only
```

Parsing `ai_capability` into `TaskDefinition` is an **additive** workflow schema extension. Existing workflow files without the field behave as today.

---

## Prompt flow

M13 uses a **minimal, domain-neutral** default prompt pipeline in `AIExecutableWorker`. Domain plugins may subclass to enrich prompts; the core does not read artifact paths or skill metadata.

### Default pipeline (core)

```
TaskDispatch
    │
    ├─ Build system prompt (fixed template + task.description)
    ├─ Build user prompt (task.name + instructions + optional task context)
    │
    ▼
GenerateRequest(prompt=..., capability=<resolved ai_capability>)
    │
    ▼
AIService.generate(request)
    │
    ▼
TaskOutcome
```

| Step | Behavior |
|------|----------|
| System prompt | States bounded execution: complete only the dispatched task; escalate if insufficient context |
| User prompt | `task.name`, `task.description`, `instructions` concatenated |
| Method | `generate()` for M13 single-shot tasks; `chat()` when subclass supplies `messages` |
| Streaming | **Not used** in M13 (`stream()` remains optional/stub) |
| Skills | Skill metadata is injected as execution guidance for `AIExecutableWorker` (M16) |
| Artifact reads | **Not in core** — domain subclasses may read files using `instructions` as project root |

### `instructions` convention

`WorkerDispatcher` populates `TaskDispatch.instructions` with workspace / project-root context string. This does not change frozen `TaskDispatch` fields — it populates an existing field.

---

## Response model

### `AIService` → `TaskOutcome` mapping

| AI result | `TaskOutcome` |
|-----------|---------------|
| `GenerateResponse` / `ChatResponse` received | `success` unless subclass validates empty content as `failure` |
| Empty content | `failure` with diagnostic message |
| Provider missing | `failure` — `"No AI provider available for capability '…'"` |
| Judgment required beyond scope | `escalation` (subclass or future policy) |

### `TaskOutcome.data` (illustrative keys)

| Key | Content |
|-----|---------|
| `provider_id` | From response |
| `model` | From response |
| `ai_capability` | Capability string used for routing |
| `content` | Model output text (M13 stores in data; domain workers may also write files) |
| `task_key` | `workflow_id.task_id` |

No change to `TaskOutcome` dataclass shape — only `data` dict contents.

---

## Error handling

| Condition | Behavior | Layer |
|-----------|----------|-------|
| No provider for capability | `TaskOutcome.failure` | `AIExecutableWorker` |
| Provider `health()` unhealthy | Optional warning in `health_check()`; execute still attempts or fails fast per worker policy | Worker |
| Provider raises exception | Propagates to `WorkerDispatcher._execute_with_worker` → `DispatchStatus.ERROR` | Existing dispatcher |
| Router config references missing provider id | Skipped silently in chain (existing router behavior) | `AIProviderRouter` |
| Partial / malformed response | `failure` or `partial` per worker validation | Worker |

**Human gates:** `task.requires_approval` is unchanged — M13 does not auto-approve. Review policy remains workflow/runtime responsibility.

---

## Retry behavior

| Scope | M13 policy | Rationale |
|-------|------------|-----------|
| Provider fallback chain | Try each provider from `resolve_chain()` once per execution | Uses existing config preferred/fallback |
| Same provider retry | **No** | Avoid duplicate spend/latency in sync dispatcher |
| Dispatcher re-dispatch | **No** | Frozen synchronous semantics |
| Exponential backoff | **No** | Deferred post-M15 job model |
| Automation `execute_worker` | Inherits worker retry policy only | No new automation action types |

---

## Provider selection

Workers **must not**:

- Import vendor SDKs
- Select providers by name in workflow TOML
- Bypass `AIService` to call `AIProvider` directly (except provider plugin internals)

Workers **must**:

- Pass a **capability string** to `AIService.generate()` / `chat()`
- Rely on `[ai]` config and `AIProviderRouter` for preferred/fallback/default ordering

Configuration example (unchanged from M12):

```toml
[ai]
default_provider = "mock-ai"

[ai.capabilities.implement]
preferred = "mock-ai"
fallback = ["mock-ai"]
```

---

## Bootstrap and `AIService` wiring

### Constraint (current bootstrap order)

```
PluginPlatform.run()  →  plugins register workers
        ↓
build_ai_service()    →  AIService created
```

Workers contributed in `register()` cannot receive `AIService` in the constructor today.

### M13 wiring pattern (implemented)

```
build_ai_service()
    ↓
worker_registry.wire_ai_service(ai_service)   # new — iterates AIExecutableWorker instances
    ↓
AutomationEngine / RuntimeContext complete
```

| Component | Change |
|-----------|--------|
| `WorkerRegistry.wire_ai_service()` | Sets service on registered `AIExecutableWorker` instances |
| `AIExecutableWorker` | Holds `AIService \| None` until wired; `execute()` fails fast if unset |
| `PluginPlatform` | **No** change to `contribute_worker` signature |
| `bootstrap()` | Call `wire_ai_service` after `build_ai_service` |

Alternative considered and **rejected** for M13: passing `AIService` into `execute()` — violates frozen worker contract.

---

## Plugin contributions (M13)

### `mock-ai` plugin (reference)

| Deliverable | Description |
|-------------|-------------|
| `MockAIWorker` or per-capability workers | `AIExecutableWorker` subclass(es) |
| Demo workflow template (optional) | Tasks with `capability = "implement"` etc. |
| Doctor / health | Worker reports unhealthy if `AIService` not wired or no provider |

Validates end-to-end path without external APIs.

### Domain plugins (software, unity)

**Not required for M13 exit criteria.** Placeholder workers remain the default.

Optional follow-up in domain plugins (post-M13):

- Subclass `AIExecutableWorker` with domain prompt templates
- Register parallel worker ids or replace placeholder `execute()` bodies
- Map `ai_capability` on existing workflow tasks

Domain-specific artifact writes stay in **plugin** code, not core.

---

## Compatibility with existing workers

| Worker family | M13 impact |
|---------------|------------|
| Git (`git.*`) | None — subprocess execution unchanged |
| Software placeholders | None by default — still touch artifact markers |
| Unity placeholders | None by default |
| Mock workers (`runtime`) | None |
| Manifest-only workers (`workers/ai/*.toml`) | Remain non-executable until plugin provides `ExecutableWorker` |
| Human workers | None |

Dispatch precedence when multiple workers share a capability: existing deterministic sort by `worker.id` — document that AI and placeholder workers **must not** register the same `work_type` unless migration intentionally replaces the placeholder.

---

## Automation compatibility

Frozen action `execute_worker` → `WorkerDispatcher.dispatch_and_execute()` → `worker.execute()`.

| Topic | M13 behavior |
|-------|--------------|
| Automation calls `AIService` directly | **Still no** — no `invoke_ai` action |
| AI execution via automation | Only through an AI-capable **worker id** |
| Rule strings (`git.status`, future `mock-ai.implement`) | Unchanged string-based coupling |

---

## Architecture freeze — what does **not** change

Per `docs/ARCHITECTURE_FREEZE_V0.5.md` and `docs/API_STABILITY.md`:

| Frozen decision | M13 respect |
|-----------------|-------------|
| Plugin-only **domain** logic | Core adds neutral `AIExecutableWorker` only; prompts/artifacts stay in plugins |
| `.vedaws/` project authority | Unchanged |
| `state.toml` authoritative | Unchanged |
| Worker **capability** matching | Unchanged — still `work_type` match |
| `TaskDispatch` / `TaskOutcome` **field sets** | Unchanged — no removed/renamed fields |
| `VedawsPlugin` + `PluginContext` contribution model | Additive wiring only |
| `AIProvider` + capability routing | Unchanged — workers use `AIService` |
| Event-driven automation | Unchanged — no new core hooks |
| Generic project template discovery | Unchanged |
| **Synchronous** event bus and dispatch | Unchanged |
| `WorkerDispatcher` public method signatures | Unchanged |
| `AIService` public method signatures | Unchanged |
| `[ai]` config shape | Unchanged |
| No vendor SDK imports in core | Unchanged |

### Deferred beyond M16

| Item | Milestone |
|------|-----------|
| `invoke_ai` automation action | Post-M16 / optional |
| Skill discovery CLI | Future |
| Nested plugin config schema validation | Future |
| Credential vault | Post-M14 |
| Async dispatch / job status | Post-M15 |
| Streaming UX / `stream()` production use | Post-M13 |
| Vendor plugins (Gemini, OpenAI, …) | Separate plugin packages |

---

## Migration notes — placeholder workers

### Software plugin (`software.*`)

**Today:** `SoftwareWorkflowWorker` matches `software-*` capabilities and touches markdown artifact markers without AI.

**Migration paths (opt-in, per task):**

| Strategy | Description |
|----------|-------------|
| **A. Parallel AI workers** | Register `software-ai.implement` with `work_type = "software-implementation"` only after removing or disabling placeholder worker for that capability |
| **B. Task `ai_capability`** | Keep placeholder worker id in workflow; swap worker implementation to `AIExecutableWorker` subclass that also writes artifacts |
| **C. Capability rename** | New workflow template version uses `capability = "implement"` + AI worker — breaking for existing projects unless both caps supported during transition |

**M13 recommendation:** Path **C** for a new demo workflow in `mock-ai`; Path **B** for software plugin migration in a later milestone.

### Unity plugin

Same pattern as software — `unity-*` capabilities vs standard AI capabilities. No Unity Editor integration.

### Manifest placeholders (`workers/ai/*.toml`)

Files under `workers/ai/` describe non-executable manifest workers (`code-generation`, etc.). They do **not** automatically become AI-bound executors. Executable AI workers come from **plugins** via `contribute_worker()`.

### Workflow templates shipped with M9/M10

Existing installed projects keep current behavior until templates are version-bumped and workers migrated.

---

## Testing strategy (M13)

| Test | Intent |
|------|--------|
| `AIExecutableWorker` unit tests | Prompt build, capability resolution, outcome mapping |
| Integration: bootstrap wires service | `wire_ai_service` called; worker execute succeeds |
| Integration: dispatch demo task | `vedaws run` dispatches `implement` → `mock-ai` |
| Regression | Git/software/unity placeholder workers unchanged |
| Doctor | AI worker binding check (provider + wiring) |

Target: extend `tests/test_ai_providers.py` and `tests/test_dispatch.py` per `016_IMPLEMENTATION_PLAN.md`.

---

## Relationship to other documents

| Document | Relationship |
|----------|--------------|
| `004_WORKERS.md` | AI worker concept; M13 specializes execution binding |
| `017_AI_PROVIDERS.md` | `AIService` / routing; M13 closes worker execute gap |
| `003_RUNTIME.md` | Bootstrap wiring order |
| `005_AUTOMATION.md` | `execute_worker` path unchanged |
| `010_PLUGINS.md` | Workers contributed via `contribute_worker` |
| `011_SKILLS.md` | Skills are consumed during AI worker execution (M16) |
| `012_CONFIGURATION.md` | `[ai]` routing unchanged |
| `015_ROADMAP.md` | M13 P0 deliverable |
| `016_IMPLEMENTATION_PLAN.md` | Exit criteria and file locations |
| `docs/API_STABILITY.md` | Frozen contracts respected |
| `docs/ARCHITECTURE_FREEZE_V0.5.md` | Frozen decisions table |

---

## Implementation checklist (post-design)

1. Implement `AIExecutableWorker` in core
2. Add `WorkerRegistry.wire_ai_service()`
3. Call wiring from `bootstrap()` after `build_ai_service()`
4. Add optional `ai_capability` to workflow parser / `TaskDefinition`
5. Contribute `mock-ai` executable worker(s) + demo workflow
6. Tests per strategy above
7. Update `017_AI_PROVIDERS.md` freeze boundary (worker binding → implemented)
8. Update `docs/API_STABILITY.md` if new public symbols (`AIExecutableWorker`, `wire_ai_service`)
9. Add `docs/MILESTONE_13_SUMMARY.md` at milestone close

---

## TODO

- Software/Unity AI migration milestones for replacing placeholder workers
- Domain-level AI prompt templates and artifact write policies in plugin workers
