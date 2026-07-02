# Vedaws Workers

**Version:** 0.5.0

**Status:** Active — v0.5 freeze (capability matching, `TaskDispatch` / `TaskOutcome` implemented)

## Purpose

This document defines the Worker model for Vedaws. Workers are the execution layer of the system: the entities that perform bounded work when the runtime dispatches tasks.

The runtime coordinates. Workers execute. This document specifies what workers are, what they declare, what they receive, what they return, how they live within orchestration, and the invariants that govern their behavior.

Workers are not a implementation technology. A worker may be a person, an AI system, a script, a service, or a development tool. The model treats them uniformly at the orchestration boundary while allowing specialization within execution.

---

## What a Worker Is

A **Worker** is any entity capable of executing a bounded unit of work and returning a structured result to the runtime.

Workers are executors, not coordinators. They perform the work defined by a dispatched task. They do not decide what happens next in a project, do not transition project state, and do not dispatch other tasks unless explicitly defined as part of their bounded task scope.

Workers exist at the boundary between orchestration and execution. The runtime selects a worker based on declared capabilities and dispatches a task. The worker accepts the task, executes within its scope, and returns a result. The runtime interprets that result; the worker does not.

### What Workers Are Not

- Workers are not the runtime.
- Workers are not workflows.
- Workers are not plugins — though plugins may register workers.
- Workers are not skills — though workers may apply skills during execution.
- Workers are not owners of project intent, direction, or accountability.

### Uniform Model, Diverse Implementations

Vedaws uses a single worker model across all executor types. The runtime interacts with workers through the same conceptual contract regardless of whether the executor is human, AI, or tool-based. Specialization appears in capability declarations and execution behavior, not in separate orchestration categories.

---

## Capabilities

**Capabilities** are how workers declare what work they can perform. Capabilities are the basis for runtime dispatch selection. The runtime matches ready tasks to workers by capability, not by identity.

### Capability Declaration

Every registered worker declares one or more capabilities. A capability describes:

| Dimension | Description |
|-----------|-------------|
| **Work type** | The class of task the worker can execute — for example, code generation, test execution, document authoring, review, or deployment verification. |
| **Scope** | The domain, artifact types, or task categories the capability covers. |
| **Constraints** | Conditions under which the capability applies or does not apply. |
| **Risk classification** | The worker's assessed risk profile for tasks in this capability — informing review requirements and automation bounds. |
| **Availability** | Whether the worker is currently able to accept dispatch. |

Capabilities are declarative. They describe what a worker *can* do, not how it does it. Execution internals remain the worker's concern.

### Capability Granularity

Capabilities should be specific enough for reliable dispatch matching and replaceability, but general enough to allow multiple workers to satisfy the same task class.

A capability that is too narrow produces irreplaceable workers. A capability that is too broad produces unreliable dispatch matches. Plugin-registered workers typically declare domain-specific capabilities; general workers declare cross-domain capabilities within their execution type.

### Capability Evolution

Workers may revise capability declarations over time. Changes to capabilities affect future dispatch only. In-flight tasks are governed by the capability match at dispatch time. Retiring a capability must not strand active tasks without explicit handling policy.

### Runtime Use of Capabilities

The runtime uses capabilities to:

- Determine which workers are eligible for a ready task.
- Prefer domain-appropriate workers when plugins are active.
- Detect when no eligible worker is available and surface blockage.
- Support replaceability by treating capabilities as the selection key.

The runtime does not inspect worker internals to infer capabilities. Undeclared capability is unavailable capability.

---

## Inputs and Outputs

Workers interact with the runtime through a dispatch contract: the runtime provides inputs; the worker returns outputs. This section defines that contract architecturally, not as an implementation specification.

### Inputs

When the runtime dispatches a task, the worker receives a **dispatch package** sufficient to execute without making orchestration decisions. Inputs include:

| Input | Description |
|-------|-------------|
| **Task definition** | The bounded work to perform: objective, expected outcome, and completion criteria. |
| **Instructions** | Specific directives for this execution within task scope. |
| **Constraints** | Boundaries the worker must not exceed — scope limits, policy restrictions, and forbidden actions. |
| **Context** | Project-relevant information needed for execution: references to related artifacts, prior task outcomes, and applicable state facts. |
| **Artifact references** | Artifacts to consume, produce, or modify as part of the task. |
| **Skill references** | Skills the worker should apply during execution, when specified by the task or workflow. |
| **Review requirements** | Whether the outcome requires human review before effects propagate. |

Inputs confer execution authority only within the dispatched task scope. They do not grant orchestration authority.

Workers must not require undeclared context to execute. If the dispatch package is insufficient, the worker returns a result indicating the deficiency rather than inferring unstated orchestration intent.

### Outputs

When execution concludes, the worker returns a **result** to the runtime. Results are orchestration inputs, not direct authority over project state. Outputs include:

| Output | Description |
|--------|-------------|
| **Outcome status** | Whether the task completed successfully, failed, was partially completed, or requires human intervention. |
| **Outcome data** | Structured information the runtime needs to evaluate success against task criteria. |
| **Artifact effects** | Artifacts created, revised, or referenced as a consequence of execution, with provenance. |
| **Scope compliance** | Declaration that execution remained within dispatched bounds, or explicit notice if bounds were insufficient. |
| **Escalation signals** | Indication that judgment beyond worker capability is required before proceeding. |
| **Diagnostics** | Information to support audit, debugging, and human review — without exposing unnecessary internal detail. |

### Result Interpretation

The runtime interprets worker results. A successful result does not automatically transition state or advance workflows unless workflow rules and policy authorize it. A failed result triggers workflow failure handling. An escalation signal routes to human judgment.

Workers do not apply their own results to project state. Result propagation is a runtime responsibility.

### Outcome Categories

| Category | Meaning | Runtime Treatment |
|----------|---------|-------------------|
| **Success** | Task completed within scope and criteria | Process through workflow rules; apply effects or queue for review as required |
| **Failure** | Task could not be completed | Record failure; apply workflow failure rules; surface for human review when required |
| **Partial** | Meaningful progress but incomplete against criteria | Treat per workflow failure or retry policy; never silently accept as success |
| **Escalation** | Worker cannot proceed without human judgment | Halt task effect propagation; surface to humans |
| **Rejection** | Dispatch package insufficient or out of scope | Return without execution; surface deficiency for runtime resolution |

---

## Lifecycle

Workers persist across tasks. Their lifecycle describes registration, availability, per-task execution, and release.

### Registration Lifecycle

| Phase | Description |
|-------|-------------|
| **Discovered** | The worker is known to the system. |
| **Registered** | The worker has declared its capabilities and is available for dispatch consideration. |
| **Deregistered** | The worker is removed from availability; active tasks require explicit handling. |

Registration is independent of any single project. Workers may be registered globally or through plugins and activated per project context.

### Per-Task Lifecycle

| Phase | Description |
|-------|-------------|
| **Available** | The worker is ready to accept a dispatched task. |
| **Assigned** | A task has been dispatched to the worker; execution has not yet begun. |
| **Executing** | The worker is actively performing the task. |
| **Returning** | The worker has concluded execution and is submitting its result. |
| **Released** | The result has been accepted by the runtime; the worker is available again. |

A worker in **Assigned** or **Executing** is bound to exactly one task.

### Lifecycle Interruptions

| Event | Worker State | Outcome |
|-------|-------------|---------|
| **Cancellation** | Assigned or Executing | Worker ceases execution; returns cancelled outcome |
| **Timeout** | Executing | Worker returns failure or partial per policy; runtime surfaces condition |
| **Unavailability** | Available → unavailable | Worker removed from dispatch pool; in-flight tasks handled per policy |
| **Deregistration** | Any | Active tasks must complete, fail, or transfer per explicit policy |

Workers do not control their own lifecycle transitions beyond reporting execution status. The runtime manages dispatch, monitoring, and release.

---

## Specialized Workers

**Specialized workers** are workers with narrow, domain-specific capability declarations. They exist to perform particular classes of work within a development domain — game engine integration, mobile build verification, infrastructure provisioning, or similar focused execution.

### Characteristics

- Declare capabilities scoped to a specific domain, artifact type, or task class.
- Typically registered through plugins that supply domain context.
- Expected to produce outcomes that satisfy domain-specific task criteria.
- May apply domain-specific skills during execution.

### Role Within the Model

Specialization does not create a separate worker category in orchestration. Specialized workers use the same model, lifecycle, and result contract as general workers. Specialization appears only in capability declarations and execution behavior.

### When Specialization Is Appropriate

Specialization is appropriate when:

- Task criteria require domain knowledge to evaluate success.
- Execution depends on domain-specific tools or conventions.
- Generic workers would produce unreliable or unverifiable outcomes.

Specialization is not appropriate when the work is domain-neutral and any capable executor within the work type would suffice.

### Boundaries

Specialized workers must not embed orchestration logic. Domain expertise informs execution; it does not determine workflow progression, state transitions, or dispatch of subsequent tasks.

---

## Human Workers

A **human worker** is a person executing a dispatched task. Human workers are first-class executors, not a fallback of last resort.

### When Humans Execute

Human workers are the right choice when:

- The task requires judgment, creativity, or acceptance authority within scope.
- The task is inherently manual — physical action, external system interaction, or subjective evaluation.
- Policy or workflow explicitly routes the task to human execution.
- Automated or AI execution has failed, escalated, or is inappropriate for the risk classification.

Dispatching to a human worker is a valid orchestration decision, not a sign of system failure.

### Human Worker Inputs

Human workers receive the same dispatch package as any worker. The package must be legible to a person: clear objective, explicit constraints, and sufficient context to act without guessing orchestration intent.

### Human Worker Outputs

Human workers return results in the same outcome categories as other workers. A human may return **Escalation** when the task as defined requires authority beyond their assigned scope — for example, architectural decisions that belong at a higher judgment level.

### Accountability

Human workers remain accountable for execution within task scope. They do not absorb project-level accountability, which stays with the humans who own project intent regardless of who executed individual tasks.

### Boundaries

Human workers do not gain orchestration authority by virtue of being human. Completing a task does not authorize state transitions unless workflow rules and policy permit. Human decision gates remain distinct from human task execution.

---

## AI Workers

An **AI worker** is a worker whose execution is performed by an artificial intelligence system. AI workers handle generative, interpretive, and analytical work within dispatched task bounds.

### When AI Workers Execute

AI workers are appropriate when:

- The task involves generation, transformation, or analysis of content within defined criteria.
- Execution benefit from adaptive reasoning within scope.
- Outcomes can be evaluated against task completion criteria, even if non-deterministic.
- Risk classification permits AI execution with or without subsequent human review.

### Non-Determinism

AI workers may produce non-deterministic outcomes. Non-determinism must be intentional, visible, and constrained by task criteria and review policy. The runtime treats AI results like any worker result — success is determined against criteria, not assumed from completion.

### Scope Discipline

AI workers are particularly susceptible to scope expansion — inferring unstated intent, making architectural decisions, or dispatching implicit follow-on work. AI workers must operate strictly within dispatched bounds and return **Escalation** when judgment beyond scope is required.

### Skills

AI workers frequently apply skills during execution. Skills provide procedural know-how; they do not expand task scope or grant orchestration authority.

### Review

Tasks with high-impact outcomes or high-risk classification may require human review of AI worker results before effects propagate, regardless of whether the AI worker reports success.

### Boundaries

AI workers are not the runtime. They do not own project state, workflow progression, or automation evaluation. They are one executor type among several, selected by capability match.

---

## Tool Workers

A **tool worker** is a worker whose execution is performed by a deterministic tool, script, or service. Tool workers handle repeatable, mechanical work with verifiable outcomes.

### When Tool Workers Execute

Tool workers are appropriate when:

- The task is deterministic and repeatable.
- Success can be verified mechanically against objective criteria.
- Execution follows a fixed procedure with predictable behavior.
- Risk classification is low and review requirements are minimal.

Examples at the architectural level: running test suites, applying formatting, executing build steps, validating schemas, or performing file transformations.

### Determinism and Reproducibility

Tool workers are the primary executors supporting Vedaws' reproducibility principle. Given the same inputs, a tool worker should produce equivalent outcomes. Deviations are failures, not variations to be silently accepted.

### Reliability

Tool workers are expected to fail clearly. Opaque failures — indeterminate exit states, unparseable output — are treated as worker failures and surfaced for resolution.

### Boundaries

Tool workers must not embed orchestration logic. A script that decides what task should run next, transitions state, or dispatches follow-on work violates worker invariants. Tools execute; the runtime orchestrates.

Tool workers are not automation rules. Automation triggers orchestration actions; tool workers execute dispatched tasks. A tool may be invoked by both, but the concepts remain distinct.

---

## Worker Replaceability

Replaceability is a core architectural requirement. The runtime must not depend on the identity of a specific worker — only on declared capabilities and returned results.

### Why Replaceability Matters

Replaceability ensures:

- No single worker becomes a hard orchestration dependency.
- Workers can be upgraded, swapped, or retired without rewriting workflows.
- Multiple providers can satisfy the same task class — different AI systems, tools, or people.
- Domain extensions through plugins do not create lock-in at the orchestration layer.

### Replaceability Requirements

| Requirement | Description |
|-------------|-------------|
| **Capability-based selection** | Dispatch selects by capability match, not worker identity. |
| **Multiple providers** | Every capability class should support multiple eligible workers where practical. |
| **Result equivalence** | Workers within the same capability class must return results the runtime can interpret uniformly. |
| **No identity binding** | Workflows and tasks reference work types and capabilities, not specific worker identities. |
| **Graceful substitution** | Replacing one worker with another capable worker requires no workflow changes. |

### When Replaceability Is Limited

Some capabilities may have only one provider in a given project context — a proprietary tool with no alternative, or a human with unique domain authority. In these cases:

- The limitation must be explicit in capability declarations.
- The runtime must surface unavailability when the sole provider is absent.
- Architecture review is required if a core workflow depends on an irreplaceable worker.

### Plugin-Registered Workers

Plugins may register specialized workers. Replaceability applies within the plugin's capability scope: multiple workers should be able to declare the same plugin-scoped capability unless exclusivity is explicit and justified.

---

## Worker Invariants

These invariants govern all workers regardless of type. Violations require architecture review.

### Execution Boundaries

1. Workers execute; they do not orchestrate.
2. Workers do not create, dispatch, or schedule tasks unless explicitly defined within bounded task scope.
3. Workers do not transition project state directly.
4. Workers do not advance workflows directly.
5. Workers do not bypass human decision gates.

### Scope

6. Workers operate only within the scope of the dispatched task.
7. Workers must not silently expand task scope.
8. Workers must return **Escalation** or **Rejection** when the dispatch package is insufficient or requires judgment beyond their capability.
9. Workers must declare scope compliance or non-compliance in their result.

### Capabilities

10. Workers must declare capabilities before being eligible for dispatch.
11. Undeclared capability is unavailable capability.
12. Capability declarations must be honest — a worker must not accept tasks outside its declared capabilities.

### Results

13. Every concluded execution must produce a result in a recognized outcome category.
14. Results are advisory to the runtime — workers do not apply their own outcomes.
15. Artifact effects reported in results must include provenance.
16. Failures must be reported explicitly, not masked as success or abandonment.

### Replaceability

17. The runtime selects workers by capability, not identity.
18. No workflow may require a specific worker identity unless explicitly authorized with documented justification.
19. Workers within the same capability class must produce runtime-interpretable results.

### Uniformity

20. Human, AI, and tool workers are subject to the same orchestration boundary.
21. Worker type affects execution behavior and risk profile, not orchestration category.
22. A human performing a task is a worker, not a separate architectural concept.

### Accountability

23. Workers are accountable for execution within task scope.
24. Workers do not absorb project-level accountability.
25. Escalation transfers judgment need to humans; it does not transfer ownership of outcomes.

### Relationship to Other Concepts

26. Skills inform worker execution; workers do not replace skills.
27. Plugins register workers; workers do not replace plugins.
28. Automation may dispatch tasks to workers; workers do not evaluate automation rules.

---

## Worker Type Summary

| Type | Primary Strength | Typical Risk Profile | Review Expectation |
|------|-----------------|---------------------|-------------------|
| **Human** | Judgment, creativity, acceptance, manual action | Varies by task | Often lower for acceptance tasks; gates may still apply |
| **AI** | Generation, interpretation, analysis within scope | Medium to high | Frequently required for high-impact outcomes |
| **Tool** | Deterministic, repeatable, verifiable execution | Low | Minimal when criteria are mechanical |
| **Specialized** | Domain-specific execution quality | Varies by domain | Per domain policy and task classification |

Worker type informs dispatch preference and review policy. It does not change the orchestration model.

---

## Relationship to Other Documents

| Document | Relationship |
|----------|--------------|
| `002_CORE.md` | Defines Worker as a core concept; this document specializes it. |
| `003_RUNTIME.md` | Defines dispatch responsibilities that consume worker capabilities and results. |
| `010_PLUGINS.md` | Plugins register workers via `contribute_worker` (implemented). |
| `011_SKILLS.md` | Skill metadata is available for worker execution guidance (M16 first consumer: `AIExecutableWorker`). |
| `008_ARTIFACTS.md` | Artifact paths and plugin-owned types; provenance registry deferred. |
| `017_AI_PROVIDERS.md` | AI providers route capability requests used by `AIExecutableWorker` execution. |

---

## TODO

- Align artifact effect reporting with `008_ARTIFACTS.md` — partial in domain plugins; cross-plugin registry deferred.
- Extend skill application beyond `AIExecutableWorker` to additional worker families.
- Define plugin worker registration with `010_PLUGINS.md`. ✅
- Define task-to-capability matching rules with workflow and dispatch. ✅ (`WorkerDispatcher`, workflow `capability` field)
- Continue plugin migration from placeholder workers to AI-capable workers where appropriate.
