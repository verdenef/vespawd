# Vedaws Core Concepts

**Version:** 0.5.0

**Status:** Active — v0.5 freeze (ten core concepts; AI routing specialized in `017_AI_PROVIDERS.md`)

## Purpose

This document defines the canonical core concepts of Vedaws. Every downstream design document, architectural decision, and extension must remain consistent with the definitions, responsibilities, lifecycles, relationships, and invariants established here.

These concepts describe *what exists* in the Vedaws model and *how those things relate*. They do not prescribe implementation.

The developer decides. Vedaws orchestrates. Workers execute. The concepts below are the vocabulary in which that relationship is expressed.

---

## Conceptual Model

Vedaws organizes development work around a **Project**. The **Runtime** coordinates that project by reading **State**, advancing **Workflows**, creating and dispatching **Tasks**, applying **Automation**, and managing **Artifacts**. **Workers** execute tasks. **Plugins** extend orchestration at the domain edge. **Skills** supply reusable know-how that workers may draw upon during execution.

```
Human Intent
     │
     ▼
  Project ◄──────────────────────────────┐
     │                                   │
     ├── State ──────► Runtime decisions │
     ├── Workflows                       │
     ├── Tasks ──────► Workers ──────────┤
     ├── Artifacts                       │
     └── Automation rules                │
            ▲                            │
            │                            │
     Plugins (extend)    Skills (inform)┘
```

---

## 1. Project

### Purpose

A **Project** is the top-level unit of orchestration in Vedaws. It represents a bounded body of development work with its own intent, state, workflows, artifacts, and lifecycle. All coordination activity in Vedaws occurs in the context of a project.

### Responsibilities

- Hold the authoritative scope of work being orchestrated.
- Own the current project state and its history of transitions.
- Contain the workflows, tasks, artifacts, and automation rules active within its boundary.
- Express human intent — goals, priorities, and constraints — in a form the runtime can coordinate against.
- Serve as the boundary for reproducibility: the same project definition and inputs should yield consistent orchestration behavior.

### Lifecycle

Project operational lifecycle is defined in **`006_STATE_MACHINE.md`**. That document is authoritative for runtime state names, transitions, and orchestration eligibility.

The summary below maps conceptual phases from earlier drafts to the canonical state machine:

| Conceptual phase | Canonical states (see 006) |
|------------------|----------------------------|
| **Created** | `created` |
| **Initialized** | `initialized` |
| **Active** (coordinating work) | `planning`, `ready`, `executing`, `awaiting_approval`, `recovering` |
| **Paused** | *Not yet implemented* — use `blocked` or explicit workflow suspension |
| **Completed** | `completed` |
| **Archived** | `archived` |

Halted conditions (`blocked`, `failed`) are operational states, not separate project concepts.

A project may return from halted states via `recovering` or replanning per `006_STATE_MACHINE.md`. **Completed** and **Archived** are terminal with respect to normal orchestration.

### Relationships

| Concept | Relationship |
|---------|--------------|
| **Runtime** | The runtime operates on exactly one active project context at a time per coordination session. |
| **State** | The project owns its state. State is meaningless outside a project boundary. |
| **Workflow** | A project contains one or more workflows that structure its work. |
| **Task** | Tasks belong to a project and are created within its workflows. |
| **Artifact** | Artifacts belong to a project and represent its durable outputs. |
| **Plugin** | Plugins extend project capabilities by registering domain-specific behavior. |
| **Automation** | Automation rules are scoped to a project and govern orchestration within it. |
| **Worker** | Workers are not owned by a project; they are dispatched to execute its tasks. |

### Invariants

- Every orchestration action occurs within a project context.
- A project always has exactly one current state.
- A project cannot be actively orchestrated without an explicit active or equivalent operational status.
- Human authority over project intent, priorities, and acceptance is never transferred to the runtime or to workers.
- A project does not implicitly inherit state or artifacts from another project.

---

## 2. Runtime

### Purpose

The **Runtime** is Vedaws' coordination layer. It is the explicit system that replaces the developer-as-implicit-runtime anti-pattern. The runtime interprets project state, advances workflows, dispatches tasks, applies automation, and maintains consistency across the project lifecycle.

### Responsibilities

- Maintain awareness of the current project state and its transition history.
- Determine what may happen next within active workflows.
- Create, schedule, and dispatch tasks to appropriate workers.
- Evaluate and apply automation rules within defined policy bounds.
- Record task outcomes and propagate their effects on state and artifacts.
- Enforce orchestration policy: sequencing, dependencies, handoffs, and human decision gates.
- Surface decisions that require human judgment rather than resolving them silently.
- Remain domain-neutral: delegate domain-specific interpretation to plugins and workers.

### Lifecycle

| Phase | Description |
|-------|-------------|
| **Inactive** | The runtime is not coordinating any project. |
| **Starting** | The runtime is loading project context, plugins, and orchestration policy. |
| **Active** | The runtime is coordinating an active project: evaluating state, dispatching tasks, applying automation. |
| **Waiting** | The runtime is active but blocked — awaiting a worker result, human decision, or external condition. |
| **Stopping** | The runtime is completing in-flight coordination and persisting state. |
| **Inactive** | Coordination has ceased. Project state is preserved. |

The runtime cycles between **Active** and **Waiting** during normal operation.

### Relationships

| Concept | Relationship |
|---------|--------------|
| **Project** | The runtime coordinates a project. It does not own project intent. |
| **State** | The runtime reads state to decide behavior and writes state transitions as authorized outcomes. |
| **Workflow** | The runtime interprets and advances workflows. |
| **Task** | The runtime creates, schedules, dispatches, and records tasks. |
| **Worker** | The runtime selects and dispatches workers; it does not execute work itself. |
| **Automation** | The runtime evaluates automation rules as part of orchestration. |
| **Artifact** | The runtime tracks artifact lifecycle events triggered by task outcomes. |
| **Plugin** | Plugins extend runtime orchestration capabilities for specific domains. |

### Invariants

- The runtime coordinates; it never executes task work directly.
- Every runtime decision about what happens next must be derivable from project state, workflow definition, and orchestration policy.
- The runtime must not assume a specific technology, language, framework, or development domain at its core.
- The runtime must not advance past a human decision gate without recorded human authorization.
- If the runtime cannot determine state or next action confidently, it must defer and surface the ambiguity — never guess silently.
- The runtime must be able to explain what it did, why, and what changed.

---

## 3. Worker

### Purpose

A **Worker** is any entity capable of executing a bounded unit of work. Workers are the executors in the Vedaws model. The runtime dispatches tasks; workers perform them.

### Responsibilities

- Accept a dispatched task with its context, instructions, and constraints.
- Execute the bounded work the task defines.
- Return a result that indicates completion, failure, or need for human intervention.
- Operate within declared capabilities without exceeding task scope.
- Produce or update artifacts when the task requires it.
- Declare when judgment beyond worker capability is required.

### Lifecycle

| Phase | Description |
|-------|-------------|
| **Registered** | The worker is known to the system and declares its capabilities. |
| **Available** | The worker is ready to accept a dispatched task. |
| **Assigned** | A task has been dispatched to the worker but execution has not begun. |
| **Executing** | The worker is actively performing the task. |
| **Completed** | The worker has returned a successful result. |
| **Failed** | The worker has returned a failure or exceeded allowed bounds. |
| **Released** | The worker is available again after completing or failing a task. |

Workers persist across tasks. Assignment and execution phases repeat per task.

### Relationships

| Concept | Relationship |
|---------|--------------|
| **Runtime** | The runtime dispatches tasks to workers and receives results. |
| **Task** | Workers execute tasks. A task is assigned to at most one worker at a time. |
| **Skill** | Workers may invoke skills to inform or structure their execution. |
| **Plugin** | Plugins may register workers and declare their capabilities. |
| **Artifact** | Workers may produce, modify, or reference artifacts as task outcomes. |
| **Project** | Workers act on behalf of a project when executing its tasks but are not owned by it. |

### Invariants

- A worker executes; it does not orchestrate.
- A worker does not own project direction, state transitions, or workflow progression.
- The runtime must not depend on the identity of a worker — only on its declared capabilities and returned results.
- A human acting on a task is a worker, not a categorically different concept.
- A worker must not silently expand task scope beyond what was dispatched.
- Multiple workers may execute tasks within the same project concurrently when workflow dependencies permit.

---

## 4. Task

### Purpose

A **Task** is a bounded unit of work within a project. It is the atomic dispatch unit of Vedaws orchestration — the specific assignment a worker receives, executes, and returns a result for.

### Responsibilities

- Express a discrete, completable unit of work with defined inputs, constraints, and expected outcomes.
- Carry sufficient context for a worker to execute without requiring orchestration judgment.
- Produce a result that the runtime can use to advance workflow and state.
- Declare dependencies on other tasks, artifacts, or state conditions where required.
- Indicate whether human review is required before its outcome takes effect.

### Lifecycle

| Phase | Description |
|-------|-------------|
| **Defined** | The task exists as part of a workflow but is not yet eligible for dispatch. |
| **Pending** | Dependencies or preconditions are not yet satisfied. |
| **Ready** | All preconditions are met; the task may be dispatched. |
| **Dispatched** | The runtime has assigned the task to a worker. |
| **Running** | The worker is executing the task. |
| **Completed** | The worker returned a successful result. |
| **Failed** | The worker returned a failure or the task could not be completed. |
| **Cancelled** | The task was explicitly cancelled before completion. |
| **Recorded** | The task outcome is persisted and its effects on state and artifacts are applied or queued for review. |

### Relationships

| Concept | Relationship |
|---------|--------------|
| **Workflow** | Tasks belong to workflows. Workflows define task structure, sequencing, and dependencies. |
| **Worker** | A task is dispatched to exactly one worker at a time. |
| **Runtime** | The runtime creates, dispatches, monitors, and records tasks. |
| **State** | Task outcomes may trigger state transitions. |
| **Artifact** | Tasks may consume, produce, or reference artifacts. |
| **Automation** | Automation may create or dispatch tasks when conditions are met. |
| **Skill** | Tasks may specify skills that inform worker execution. |
| **Project** | Tasks belong to exactly one project. |

### Invariants

- Every task belongs to exactly one project and one workflow.
- A task must have a completable definition before dispatch.
- A task in **Running** state is assigned to exactly one worker.
- A completed or failed task must produce a recorded outcome before its effects propagate.
- Tasks that affect high-impact state or artifacts must respect human review gates defined by workflow or policy.
- A task does not dispatch itself; creation and dispatch are runtime responsibilities.

---

## 5. Workflow

### Purpose

A **Workflow** is a structured model of how work progresses within a project. It defines the tasks, their relationships, sequencing rules, decision gates, and the conditions under which the project advances. Workflows are the primary instrument of orchestration.

### Responsibilities

- Define the ordered and parallel structure of tasks within a project phase or concern.
- Express dependencies, preconditions, and completion criteria between tasks.
- Identify decision gates that require human judgment before progression.
- Map task outcomes to state transitions.
- Provide a legible model of project progression that humans can inspect and reason about.
- Support reproducibility by defining orchestration structure independently of individual worker behavior.

### Lifecycle

| Phase | Description |
|-------|-------------|
| **Defined** | The workflow structure exists but is not yet active within a project. |
| **Activated** | The workflow is in effect for the project and the runtime may create and advance its tasks. |
| **In Progress** | At least one task is pending, ready, dispatched, or running within the workflow. |
| **Blocked** | Progress is halted pending a dependency, human decision, or external condition. |
| **Completed** | All required tasks are completed and completion criteria are satisfied. |
| **Cancelled** | The workflow is terminated before completion. |

A project may have multiple workflows. They may be active concurrently when their concerns are independent.

### Relationships

| Concept | Relationship |
|---------|--------------|
| **Project** | Workflows belong to a project and structure its orchestrated work. |
| **Task** | Workflows contain tasks and define their relationships. |
| **State** | Workflow progression drives and is constrained by project state. |
| **Runtime** | The runtime interprets and advances workflows. |
| **Automation** | Automation operates within workflow structure, not outside it. |
| **Plugin** | Plugins may provide domain-specific workflow definitions and extensions. |

### Invariants

- Every workflow belongs to exactly one project.
- Workflow progression must be derivable from task outcomes and defined transition rules.
- A workflow must not contain circular dependencies that cannot be resolved.
- Human decision gates within a workflow cannot be bypassed by automation or worker action.
- A workflow defines structure; it does not execute work directly.
- Multiple active workflows within a project must have explicitly defined interaction rules or remain independent.

---

## 6. State

### Purpose

**State** is the explicit, authoritative representation of where a project stands at any moment. It is the foundation of state-driven orchestration: the runtime derives behavior from state rather than from implicit assumptions or scattered context.

### Responsibilities

- Represent the current position and condition of a project within its workflows.
- Record the history of transitions for audit, reproducibility, and legibility.
- Provide the basis for automation evaluation and task readiness.
- Surface conditions that require human attention or decision.
- Distinguish between operational facts the runtime maintains and external truths it integrates with.

### Lifecycle

| Phase | Description |
|-------|-------------|
| **Initialized** | The project has a defined initial state. |
| **Current** | The state is active and authoritative for runtime decisions. |
| **Transitioning** | A state change is in progress — triggered by a task outcome, human decision, or automation. |
| **Stabilized** | The transition is complete; the new state is current. |
| **Terminal** | The project has reached a terminal state such as completed or archived. |

State transitions repeat throughout the project lifecycle. **Terminal** states admit no further orchestration transitions.

### Relationships

| Concept | Relationship |
|---------|--------------|
| **Project** | State belongs to a project. A project has exactly one current state. |
| **Runtime** | The runtime reads current state and authorizes transitions. |
| **Workflow** | State constrains which workflows are active; workflow progression updates state. |
| **Task** | Task outcomes may trigger state transitions. |
| **Automation** | Automation rules evaluate state conditions to determine actions. |
| **Artifact** | State may reference artifact conditions as preconditions or outcomes. |

### Invariants

- A project always has exactly one current state.
- State transitions must be explicit, recorded, and attributable to a cause: task outcome, human decision, or authorized automation.
- The runtime must not act on assumed or unstated state.
- State must be legible: a human must be able to inspect current state and understand why it is what it is.
- State transitions that affect human-authority domains require recorded human authorization.
- Historical state must not be silently altered; corrections are new transitions with recorded rationale.

---

## 7. Artifact

### Purpose

An **Artifact** is a durable product of development work within a project. Artifacts are the tangible outputs — documents, specifications, generated content, configuration, reports, and other persisted results — that tasks and workers produce and that subsequent work may depend upon.

### Responsibilities

- Represent durable outputs that exist beyond a single task execution.
- Provide referencable inputs for downstream tasks and workflows.
- Maintain provenance: which task or worker produced or last modified the artifact.
- Support versioning or revision history sufficient for reproducibility and audit.
- Distinguish Vedaws-managed artifact metadata from external sources of truth the project integrates with.

### Lifecycle

| Phase | Description |
|-------|-------------|
| **Declared** | An artifact is anticipated by workflow or task definition but not yet produced. |
| **Created** | The artifact is first produced by a task or worker outcome. |
| **Active** | The artifact is the current authoritative version for its role in the project. |
| **Revised** | A subsequent task or worker has produced a new version or modification. |
| **Deprecated** | The artifact is superseded or no longer used in active workflows. |
| **Archived** | The artifact is retained for history but excluded from active orchestration. |

### Relationships

| Concept | Relationship |
|---------|--------------|
| **Project** | Artifacts belong to a project. |
| **Task** | Tasks produce, consume, and reference artifacts. |
| **Worker** | Workers create and modify artifacts as task outcomes. |
| **Workflow** | Workflows declare artifact dependencies and expected outputs. |
| **State** | State may reference artifact existence or properties as conditions. |
| **Skill** | Skills may reference artifact types or templates as execution guidance. |
| **Runtime** | The runtime tracks artifact lifecycle events; it does not replace external artifact stores. |

### Invariants

- Every artifact belongs to exactly one project.
- An artifact must have recorded provenance linking it to the task or authorized action that produced it.
- Artifacts referenced by ready or running tasks must exist or be explicitly marked as pending creation.
- The runtime must not claim authority over external systems it does not govern; it tracks integration, not ownership of external truth.
- Deprecation and archival must not silently remove artifacts that active tasks depend upon.
- Artifact revision must not destroy audit history of prior versions.

---

## 8. Plugin

### Purpose

A **Plugin** is a domain-specific extension to Vedaws orchestration capabilities. Plugins keep the runtime small and domain-neutral by supplying specialized behavior — workers, workflows, state semantics, and domain interpretation — at the edge rather than in the core.

### Responsibilities

- Register domain-specific workers and their declared capabilities.
- Provide workflow definitions and extensions appropriate to a development domain.
- Supply domain-specific state semantics and transition rules within core invariants.
- Interpret domain context for the runtime without embedding domain knowledge in the core.
- Declare compatibility requirements and boundaries so the runtime can evaluate whether the plugin may be activated for a project.

### Lifecycle

| Phase | Description |
|-------|-------------|
| **Discovered** | The plugin is known to the system. |
| **Registered** | The plugin is declared with its capabilities and compatibility requirements. |
| **Activated** | The plugin is enabled for a project and its extensions are in effect. |
| **Active** | The plugin is contributing workers, workflows, or semantics to orchestration. |
| **Deactivated** | The plugin is disabled for a project; its extensions are no longer applied to new orchestration. |
| **Retired** | The plugin is removed from availability. Existing project references must be handled explicitly. |

### Relationships

| Concept | Relationship |
|---------|--------------|
| **Runtime** | Plugins extend runtime orchestration capabilities. |
| **Project** | Plugins are activated per project, not globally assumed. |
| **Worker** | Plugins register workers and declare their capabilities. |
| **Workflow** | Plugins provide domain-specific workflow definitions. |
| **State** | Plugins may extend state with domain-specific dimensions within core invariants. |
| **Task** | Plugins influence task definitions through workflow extensions. |
| **Skill** | Plugins may bundle or reference skills appropriate to their domain. |

### Invariants

- Plugins extend the runtime; they do not replace it.
- Core orchestration invariants hold regardless of which plugins are active.
- A plugin must declare its capabilities and compatibility boundaries before activation.
- Deactivating a plugin must not corrupt project state; active orchestration must degrade gracefully or block with explicit notice.
- Domain-specific behavior belongs in plugins, not in the core runtime.
- Plugins must not bypass human decision gates or automation policy bounds defined by the core model.

---

## 9. Skill

### Purpose

A **Skill** is a reusable package of specialized know-how that informs how a worker executes a task. Skills encode procedural knowledge, conventions, and domain expertise in a form that workers can draw upon without the runtime or workflow needing to embed that knowledge directly.

Skills address the distinction between *orchestration* (what happens, when, and in what order) and *execution guidance* (how to perform a specific kind of work well).

### Responsibilities

- Provide structured know-how that workers apply during task execution.
- Encode repeatable procedures, conventions, and quality criteria for a class of work.
- Remain reusable across tasks, workflows, and projects within their declared scope.
- Declare their applicability so workers and the runtime can determine when a skill is relevant.
- Stay subordinate to task scope and human authority — a skill guides execution, it does not redefine orchestration.

### Lifecycle

| Phase | Description |
|-------|-------------|
| **Defined** | The skill is authored with its scope and applicability. |
| **Published** | The skill is available for use by workers. |
| **Referenced** | A task or worker invocation specifies the skill as execution guidance. |
| **Applied** | The worker uses the skill during task execution. |
| **Updated** | The skill is revised; applicability and versioning are managed explicitly. |
| **Retired** | The skill is withdrawn from use; active references must be handled explicitly. |

### Relationships

| Concept | Relationship |
|---------|--------------|
| **Worker** | Workers apply skills during task execution. |
| **Task** | Tasks may specify which skills inform their execution. |
| **Plugin** | Plugins may provide skills as part of domain-specific capability. |
| **Artifact** | Skills may reference artifact types, templates, or conventions. |
| **Workflow** | Workflows may require specific skills for certain task types. |
| **Runtime** | The runtime may validate skill applicability at dispatch but does not execute skills. |

### Invariants

- Skills inform execution; they do not orchestrate, dispatch tasks, or transition state.
- A skill must declare its scope and applicability.
- Applying a skill must not expand task scope beyond what the runtime dispatched.
- Skills are reusable across contexts; they are not task instances.
- Retiring a skill must not silently break active tasks that depend upon it.
- Skills are not a substitute for workflows, automation, or project coordination.

---

## 10. Automation

### Purpose

An **Automation** is a declared rule that triggers orchestration actions when defined conditions are met. Automation eliminates toil by handling deterministic, repeatable, low-risk coordination and execution patterns without requiring manual invocation each time.

Automation serves orchestration. It operates within workflow structure and policy bounds; it is not a parallel system of behavior.

### Responsibilities

- Evaluate conditions against project state and artifact properties.
- Trigger authorized actions: task creation, task dispatch, state transitions, or notifications.
- Operate within policy bounds that define risk tolerance and human visibility requirements.
- Produce traceable records of what was triggered, why, and what resulted.
- Defer to human review when conditions are ambiguous, outcomes are high-impact, or policy requires it.

### Lifecycle

| Phase | Description |
|-------|-------------|
| **Defined** | The automation rule is authored with conditions, actions, and policy classification. |
| **Enabled** | The automation is active and may be evaluated by the runtime. |
| **Evaluated** | The runtime checks whether conditions are met. |
| **Triggered** | Conditions are satisfied and the automation initiates its declared action. |
| **Executed** | The triggered action has been carried out. |
| **Recorded** | The automation event and its outcome are persisted for audit. |
| **Disabled** | The automation is inactive; it is not evaluated until re-enabled. |

### Relationships

| Concept | Relationship |
|---------|--------------|
| **Runtime** | The runtime evaluates and executes automation within policy bounds. |
| **State** | Automation conditions are evaluated against project state. |
| **Task** | Automation may create, dispatch, or advance tasks. |
| **Workflow** | Automation operates within workflow structure and respects its gates. |
| **Worker** | Automation may dispatch tasks to workers but does not replace them. |
| **Artifact** | Automation conditions may reference artifact properties. |
| **Project** | Automation rules are scoped to a project. |

### Invariants

- Automation serves orchestration; it does not replace the runtime.
- Every automation must have explicit conditions and declared actions.
- Automation must not bypass human decision gates or high-impact review requirements.
- Every triggered automation must produce a traceable record.
- Disabled automation must not fire silently or partially.
- Automation must not transfer human accountability; humans remain responsible for project outcomes.
- When conditions are ambiguous or policy classification is uncertain, automation must defer rather than proceed.

---

## Cross-Concept Summary

| Concept | Primary Role | Owned By | Executes Work |
|---------|-------------|----------|---------------|
| **Project** | Scope and boundary of orchestration | — | No |
| **Runtime** | Coordination and dispatch | — | No |
| **Worker** | Task execution | — | Yes |
| **Task** | Bounded dispatch unit | Project / Workflow | No |
| **Workflow** | Structure of progressing work | Project | No |
| **State** | Authoritative project position | Project | No |
| **Artifact** | Durable output | Project | No |
| **Plugin** | Domain extension of orchestration | — | No |
| **Skill** | Reusable execution know-how | — | No |
| **Automation** | Condition-driven orchestration rule | Project | No |

---

## Architectural Constraints

The following constraints apply to all core concepts collectively. Any design that violates them requires architecture review per the escalation rules.

1. **Coordination and execution remain separated.** Only workers execute task work.
2. **State is always explicit.** No concept may depend on implicit or unstated project context.
3. **Human authority is preserved.** State transitions, workflow gates, and high-impact automation defer to humans.
4. **Domain neutrality is maintained at the core.** Domain specificity flows through plugins, workers, and skills.
5. **Everything is traceable.** Tasks, state transitions, automation events, and artifact changes are recorded with cause.
6. **Reproducibility is a first-class concern.** Concepts support consistent behavior given the same inputs.
7. **New concepts require architecture review.** The ten concepts in this document are the canonical set until explicitly extended.

---

## TODO

- Define formal state machine semantics in `006_STATE_MACHINE.md`. ✅
- Expand project structure and boundaries in `007_PROJECT_MODEL.md`. ✅
- Detail artifact taxonomy and provenance rules in `008_ARTIFACTS.md` — plugin-owned artifacts at v0.5; generic registry deferred.
- Resolve plugin and skill boundaries in `010_PLUGINS.md`. ✅
- Align automation policy classification in `005_AUTOMATION.md` — rule engine and actions implemented; formal risk tiers deferred.
- Memory remains out of scope at v0.5 (`009_MEMORY.md`); not a core concept until architecture review.
