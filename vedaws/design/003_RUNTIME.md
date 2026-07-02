# Vedaws Runtime

**Version:** 0.5.0

**Status:** Active — v0.5 freeze baseline with M13–M15 hardening

## Purpose

The **Runtime** is the orchestration layer of Vedaws. It is the explicit system that replaces the developer-as-implicit-runtime anti-pattern described in the Vision and Philosophy documents.

Where developers today manually remember project state, decide the next step, coordinate tools, reconcile outputs, and maintain workflow consistency, the runtime performs that coordination role as a first-class architectural concern.

The runtime exists to answer orchestration questions:

- Where does this project stand right now?
- What work is eligible to happen next?
- Who should execute it?
- What happens when it completes, fails, or requires human judgment?
- How do workflows, automation, and plugins fit together without contradiction?

The runtime does not answer execution questions. Workers answer those. The runtime does not answer intent questions. Humans answer those.

The developer decides. Vedaws orchestrates. Workers execute. The runtime is Vedaws' orchestration.

---

## Responsibilities

The runtime bears responsibility for coordination across the full project lifecycle. Its responsibilities are orchestration responsibilities only.

### Core Coordination

- Operate within a project context as the active coordination authority.
- Maintain a coherent view of project state, active workflows, pending and in-flight tasks, and registered extensions.
- Determine eligible next actions from state, workflow definitions, and orchestration policy.
- Create, schedule, dispatch, monitor, and record tasks.
- Evaluate and apply automation rules within defined policy bounds.
- Enforce sequencing, dependencies, handoffs, and human decision gates.
- Propagate authorized task outcomes to workflow progression, state transitions, and artifact lifecycle events.

### Consistency and Legibility

- Ensure orchestration behavior is derivable from explicit inputs, not hidden assumptions.
- Preserve a traceable record of coordination decisions and their causes.
- Surface ambiguity, conflict, and blocked conditions to humans rather than resolving them silently.
- Explain what the runtime did, why, and what changed.

### Boundary Enforcement

- Preserve the separation between coordination and execution.
- Preserve human authority over judgment, acceptance, and strategic direction.
- Remain domain-neutral at its core; delegate domain interpretation to plugins and domain execution to workers.
- Integrate with external systems without claiming authority over truths it does not govern.

### Extension Coordination

- Load, activate, and coordinate plugins for a project within declared compatibility boundaries.
- Incorporate plugin contributions — workers, workflows, state dimensions, and domain rules — into orchestration without allowing plugins to override core invariants.
- Validate that plugin-provided behavior remains consistent with active project state and orchestration policy.

---

## What the Runtime Owns

Ownership here means *authority and accountability within the orchestration layer*. The runtime owns coordination artifacts and decisions, not project intent or execution products.

### Orchestration Process

The runtime owns the active coordination session: whether orchestration is running, waiting, or stopped for a given project context.

### Coordination State

The runtime owns the *process* of reading, evaluating, and authorizing state transitions. The project owns state as a concept; the runtime owns the orchestration authority to apply authorized transitions and record them.

### Task Orchestration Lifecycle

The runtime owns the orchestration lifecycle of tasks: creation eligibility, readiness evaluation, dispatch, monitoring, completion recording, and effect propagation. It does not own task execution itself.

### Dispatch Decisions

The runtime owns the decision of which worker receives a ready task, based on declared capabilities, availability, workflow constraints, and orchestration policy — not on worker identity as a hard binding.

### Workflow Progression Authority

The runtime owns the authority to advance workflow position based on recorded task outcomes, authorized automation, and human decisions. It does not own workflow definitions; those belong to the project.

### Automation Evaluation

The runtime owns the evaluation and triggering of automation rules within policy bounds. Automation rules belong to the project; the runtime owns their orchestration-time application.

### Orchestration Policy Enforcement

The runtime owns enforcement of core orchestration policy: dependency satisfaction, gate compliance, concurrency rules, and review requirements.

### Coordination Audit Trail

The runtime owns the record of coordination events: dispatches, state transitions it applied, automation triggers, blocks, escalations, and errors encountered during orchestration.

### Event Bus (Milestone 8)

The runtime owns an in-process **Event Bus** for loose coupling between orchestration components:

- **Publish** — state, workflow, task, worker, and plugin lifecycle emit typed events.
- **Subscribe** — plugins subscribe via the Plugin SDK; core components wire publishers at integration points.
- **Synchronous dispatch** — handlers run inline during `publish()`; async/remote messaging is out of scope.

Events are immutable value objects with `id`, `type`, `timestamp`, `source`, `payload`, optional `correlation_id`, and `metadata`.

System event types include: `ProjectInitialized`, `ProjectStateChanged`, `WorkflowStarted`, `WorkflowCompleted`, `TaskCreated`, `TaskStarted`, `TaskCompleted`, `TaskFailed`, `WorkerRegistered`, `WorkerStarted`, `WorkerCompleted`, `PluginLoaded`, `PluginUnloaded`. Custom types are allowed.

Implementation: `runtime/vedaws/events/`. CLI: `vedaws events`.

---

### Automation Engine (Milestone 11)

The runtime owns an **Automation Engine** that reacts to bus events with data-driven rules:

- **Subscribe** — engine registers for event types referenced by active rules.
- **Evaluate** — optional conditions matched against `event.payload` (all must match).
- **Execute** — ordered actions via `ActionExecutor` (`execute_worker`, `publish_event`, `transition_state`, `workflow_step`, `plugin_command`).
- **Guards** — `automation_depth` limits nested `publish_event`; re-entrant rule chains detected.

Rules load from plugin contributions (`contribute_automation_rule`) and `.vedaws/automation.toml`. Project rules override plugin rules with the same `id`.

Bootstrap wires `AutomationEngine` after `AIService` is built. The engine receives `event_bus`, project context, dispatcher, worker registry, and plugin registry.

Implementation: `runtime/vedaws/automation/`. CLI: `vedaws automation`. See `005_AUTOMATION.md`.

---

### AI Service (Milestone 12, bound in M13)

The runtime exposes **AIService** on `RuntimeContext` for capability-based AI requests:

- **Registry** — plugin-contributed `AIProvider` implementations (`contribute_ai_provider`).
- **Routing** — `[ai]` config selects preferred/fallback/default provider per capability (`chat`, `plan`, `implement`, …).
- **Facade** — `chat()`, `generate()`, `stream()`, `embeddings()` resolve a provider without vendor imports in core.

`AIService` is wired during bootstrap via `build_ai_service()`. Reference provider: `plugins/mock-ai/`.

**M13 update:** AI-capable workers invoke `AIService` via `AIExecutableWorker` while preserving capability-based worker dispatch and plugin-owned providers.

Implementation: `runtime/vedaws/ai/`. CLI: `vedaws ai`. See `017_AI_PROVIDERS.md`.

---

### Bootstrap order (implemented)

```
load_config → setup_logging → EventBus
  → discover_workers → WorkerRegistry (+ mock workers)
  → PluginPlatform.run() → plugin contributions merged
  → detect_project() → wire_project_events
  → WorkerDispatcher (if project + workflow engine)
  → build_ai_service() → AIService
  → AutomationEngine (rules from plugins + automation.toml)
  → RuntimeContext
```

Public entry: `vedaws.runtime.bootstrap.bootstrap()` / `shutdown()`.

---

### Active Extension Registry

The runtime owns the active view of which plugins are registered and activated for the current project context, and how their contributions participate in orchestration.

---

## What the Runtime Must Never Own

These boundaries are architectural. Violating them requires architecture review.

### Project Intent

The runtime must never own *why* a project exists, what it should become, or what tradeoffs are acceptable. Intent belongs to humans and is expressed through the project.

### Human Judgment and Acceptance

The runtime must never own decisions that require strategic, architectural, creative, or acceptance judgment. It surfaces these decisions; it does not make them.

### Task Execution

The runtime must never execute task work directly. Execution belongs exclusively to workers. The runtime dispatches; it does not perform.

### Worker Internals

The runtime must never own how a worker accomplishes its work — model selection, tool invocation strategy, prompting, or procedural steps during execution. Workers and skills own execution behavior.

### Domain Expertise

The runtime must never embed domain-specific knowledge at its core. Domain semantics belong in plugins, workers, and skills.

### External Sources of Truth

The runtime must never claim ownership of external systems it does not govern: version control history, IDE buffers, cloud deployments, model weights, engine project files, and similar external stores. It integrates with and tracks references to them; it does not replace them.

### Artifact Content

The runtime tracks artifact lifecycle and provenance within orchestration. It does not own the underlying content of artifacts held in external systems.

### Accountability for Outcomes

The runtime must never absorb accountability for project outcomes. Humans remain responsible. The runtime is responsible for coordination correctness and legibility, not for the creative or strategic success of the work product.

### Implicit Context

The runtime must never treat conversation history, undocumented assumptions, or stale tool state as authoritative project state. If it is not explicit, the runtime does not own it as truth.

### Plugin Authority Over Core Invariants

The runtime must never delegate to plugins the authority to override human gates, core invariants, or orchestration policy bounds.

---

## State Management Responsibilities

State management is central to the runtime. The runtime is state-driven: behavior emerges from explicit project state, not from inference.

### Reading State

- Treat the project's current state as the primary input to orchestration decisions.
- Evaluate task readiness, workflow eligibility, and automation conditions against current state.
- Incorporate plugin-provided state dimensions only when those plugins are active and their semantics are registered.

### Authorizing Transitions

- Apply state transitions only when authorized by: a recorded task outcome, a recorded human decision, or an automation rule within policy bounds.
- Ensure every transition is attributable to a specific cause.
- Block transitions that would violate human decision gates or orchestration policy.

### Recording History

- Preserve transition history for audit, reproducibility, and legibility.
- Never silently alter historical state; corrections are new transitions with recorded rationale.

### Handling Ambiguity

- When state is inconsistent, incomplete, or insufficient to determine the next action, halt progression and surface the condition to humans.
- Never infer state from implicit context or assume missing information.

### Distinguishing Owned vs Integrated State

- Maintain clear separation between state the runtime governs as part of orchestration and external conditions it observes but does not own.
- Reflect external changes only through defined integration paths, not silent adoption.

### Terminal State Respect

- Cease active orchestration when the project reaches terminal state.
- Prevent unauthorized transitions out of terminal states without explicit human authorization.

---

## Worker Dispatch Responsibilities

Worker dispatch is the runtime's primary mechanism for connecting orchestration to execution.

### Readiness Evaluation

- Identify tasks that have satisfied all preconditions and dependencies.
- Verify that required artifacts exist or are explicitly marked as pending creation.
- Confirm that human review gates preceding dispatch have been cleared where required.

### Worker Selection

- Select workers by declared capability match, not by hard-coded identity.
- Prefer workers registered through active plugins when domain-specific capability is required.
- Support human workers as first-class dispatch targets when judgment or manual action is appropriate.

### Dispatch Packaging

- Provide each dispatched task with sufficient context, instructions, constraints, and references for the worker to execute without making orchestration decisions.
- Include applicable skill references when the workflow or task definition requires them.
- Scope dispatch narrowly; workers must not need to infer unstated orchestration intent.

### Monitoring

- Track dispatched and running tasks until a result is returned or a timeout or cancellation policy applies.
- Detect stalled, orphaned, or out-of-scope execution and escalate according to error handling philosophy.
- Apply bounded retry loops at orchestration level when the failure mode is non-destructive and deterministic (for example, eligibility/no-worker re-evaluation in run loops).

### Result Processing

- Accept worker results as input to orchestration, not as direct authority over state.
- Validate that results are structurally usable before propagating effects.
- Queue outcomes that require human review before their effects take hold.

### Concurrency

- Permit parallel dispatch when workflow dependencies allow.
- Prevent race conditions that would violate sequencing rules or produce inconsistent state.

At v0.5/M15, execution remains **synchronous** and single-threaded. M15 hardening improves deterministic run-loop behavior and diagnostics without introducing async transport, distributed workers, or job queues.

### Replaceability

- Ensure no dispatch path assumes a single irreplaceable worker. Capability declarations are the selection basis.

---

## Workflow Progression Responsibilities

Workflows are the structural instrument of orchestration. The runtime interprets and advances them; it does not redefine them at execution time.

### Activation and Scope

- Activate workflows according to project state and human authorization.
- Track which workflows are active, blocked, completed, or cancelled within the project.
- Respect independence or explicit interaction rules when multiple workflows are active concurrently.

### Task Graph Management

- Instantiate tasks defined by workflows as they become eligible.
- Evaluate dependencies and preconditions before promoting tasks from pending to ready.
- Prevent dispatch of tasks whose prerequisites are unsatisfied.

### Gate Enforcement

- Halt progression at human decision gates until recorded authorization is present.
- Halt progression at review gates until required approval is recorded.
- Never allow workers or automation to bypass workflow gates.

### Outcome Propagation

- Map recorded task outcomes to workflow transition rules.
- Advance, block, branch, or complete workflows based on defined rules and actual outcomes.
- Reflect workflow progression in project state through authorized transitions.

### Blockage Detection

- Identify workflows that cannot progress due to failed tasks, missing artifacts, unavailable workers, or unresolved human decisions.
- Surface blocked workflows explicitly rather than leaving them in ambiguous in-progress status.

### Completion

- Mark workflows completed only when defined completion criteria are satisfied.
- Prevent premature completion that would leave required work orphaned.

---

## Plugin Coordination Responsibilities

Plugins extend orchestration at the domain edge. The runtime coordinates plugins; plugins do not coordinate the runtime.

### Discovery and Registration

- Maintain awareness of available plugins and their declared capabilities, compatibility requirements, and boundaries.
- Reject or defer activation of plugins whose requirements are incompatible with the current project context.

### Per-Project Activation

- Activate plugins explicitly per project, not by global assumption.
- Record which plugins are active for the current orchestration context.

### Contribution Integration

- Incorporate plugin-registered workers into dispatch selection pools.
- Incorporate plugin-provided workflow definitions and extensions into active orchestration.
- Incorporate plugin-provided state dimensions and transition semantics within core invariants.

### Conflict Resolution

- Detect conflicts between plugin contributions and core orchestration policy or between multiple active plugins.
- Resolve conflicts by blocking with explicit notice, not by silent precedence rules that obscure behavior.

### Deactivation Safety

- Deactivate plugins without corrupting project state.
- Ensure deactivation does not strand in-flight tasks without explicit handling policy.
- Prevent deactivated plugins from affecting new orchestration while honoring recorded historical contributions.

### Invariant Preservation

- Verify that plugin behavior does not bypass human gates, violate state invariants, or introduce domain assumptions into the core runtime.
- Treat plugins as extensions, not replacements.

---

## Error Handling Philosophy

The runtime's approach to errors reflects Vedaws' commitment to legibility, human authority, and coordination over silent recovery.

### Fail Visible, Not Silent

Errors during orchestration must be recorded and surfaced. The runtime must not swallow failures, guess at recovery, or proceed as though an error did not occur.

### Fail Stopped, Not Corrupt

When the runtime cannot proceed safely, it stops orchestration progression rather than applying partial or speculative state changes. A blocked project with explicit cause is preferable to an advancing project with hidden inconsistency.

### Distinguish Error Classes

The runtime treats errors differently based on their nature:

| Class | Description | Runtime Stance |
|-------|-------------|----------------|
| **Precondition failure** | A task or transition was requested but prerequisites are not met | Block and report; do not dispatch or transition |
| **Worker failure** | A worker returned failure or exceeded bounds | Record outcome; apply workflow failure rules; surface for human review when required |
| **Policy violation** | An action would breach gates, invariants, or automation bounds | Reject the action; record the violation; surface to humans |
| **Ambiguity** | State or inputs are insufficient to decide safely | Halt and request human clarification |
| **Integration failure** | An external system required for orchestration is unavailable | Block affected paths; continue independent paths only when safe and explicit |
| **Plugin conflict** | Active plugins or contributions are incompatible | Block activation or affected orchestration; require explicit resolution |
| **Internal inconsistency** | Orchestration records are contradictory | Halt orchestration; surface for architecture-level review |

### Prefer Deferral Over Speculation

When error recovery would require guessing intent, inferring missing state, or bypassing gates, the runtime defers to human judgment instead of auto-recovering.

### Preserve Auditability

Every error, block, rejection, and recovery path must be recorded with sufficient context for a human to understand what happened and what options exist.

### Recovery Is Explicit

Resumption after error requires explicit authorization — human decision, defined retry policy, or authorized automation within low-risk bounds. The runtime does not auto-retry high-impact failures without policy.

### Worker Failures Are Not Runtime Failures

A task failure is an orchestration input, not necessarily a runtime malfunction. The runtime processes worker failures through workflow rules; it does not conflate execution failure with coordination collapse unless orchestration integrity is compromised.

### Graceful Degradation at the Edge

When domain-specific capability is unavailable due to plugin or worker unavailability, the runtime may continue unaffected orchestration paths. Degradation must be explicit and bounded, not silent partial operation.

---

## Invariants

These invariants govern the runtime at all times. They are non-negotiable unless changed through architecture review.

### Coordination and Execution

1. The runtime coordinates; it never executes task work.
2. Only workers execute dispatched tasks.
3. Every dispatch decision is recorded.

### State

4. The runtime acts only on explicit, current project state.
5. Every state transition applied by the runtime has a recorded cause.
6. Historical state is never silently modified.
7. Ambiguous state halts progression.

### Human Authority

8. Human decision gates are never bypassed by the runtime, workers, automation, or plugins.
9. High-impact outcomes require recorded human authorization before taking effect where policy demands it.
10. The runtime surfaces judgment decisions; it does not make them.

### Domain Neutrality

11. The runtime core contains no domain-specific orchestration logic.
12. Domain behavior enters only through plugins, workers, and skills.
13. Worker selection is capability-based, not identity-based.

### Workflows and Tasks

14. Task dispatch requires satisfied preconditions and a completable task definition.
15. A running task is assigned to exactly one worker at a time.
16. Workflow progression is derivable from recorded outcomes and defined rules.
17. Tasks do not self-dispatch.

### Automation

18. Automation is evaluated by the runtime within policy bounds.
19. Automation never bypasses gates or overrides invariants.
20. Every automation trigger is recorded.

### Plugins

21. Plugins extend the runtime; they do not replace it.
22. Core invariants hold regardless of active plugins.
23. Plugin deactivation must not corrupt project state.

### Legibility and Accountability

24. The runtime must be able to explain any coordination action after the fact.
25. Errors block or record; they do not silently disappear.
26. The runtime does not absorb human accountability for project outcomes.

### External Systems

27. The runtime integrates with external truth; it does not claim ownership of it.
28. External state is adopted only through defined integration paths.

---

## Relationship to Other Documents

| Document | Relationship |
|----------|--------------|
| `002_CORE.md` | Defines Runtime as a core concept; this document specializes it. |
| `006_STATE_MACHINE.md` | State transition semantics and eligibility (`006` Active at v0.5). |
| `004_WORKERS.md` | Worker model, `TaskDispatch` / `TaskOutcome` dispatch contract. |
| `005_AUTOMATION.md` | Automation engine, rules, and actions (implemented M11). |
| `010_PLUGINS.md` | Plugin platform, contributions, and activation. |
| `017_AI_PROVIDERS.md` | AI provider SDK and routing (implemented M12). |

---

## TODO

- Formalize state transition rules in `006_STATE_MACHINE.md`. ✅
- Define worker result and capability contracts in `004_WORKERS.md`. ✅
- Define automation policy tiers in `005_AUTOMATION.md` — actions implemented; formal risk-tier taxonomy deferred.
- Define plugin activation and conflict resolution in `010_PLUGINS.md`. ✅
- Async event bus / job model for long-running work — deferred post-M15 (`015_ROADMAP.md`).
