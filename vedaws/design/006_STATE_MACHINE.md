# Vedaws State Machine

**Version:** 0.5.0

**Status:** Active — v0.5 freeze (11 states, file-backed `state.toml`, workflow bridge)

## Purpose

This document defines the canonical **project state machine** for Vedaws. It formalizes the operational states a project may occupy, the valid transitions between them, the rules governing those transitions, and the invariants that must hold at all times.

Project state is the primary input to runtime orchestration. Workflows, tasks, automation, and dispatch eligibility are all interpreted in the context of the project's current state. If state is ambiguous or inconsistent, orchestration halts.

This document defines workflow semantics — what states mean and how projects move between them. It does not prescribe implementation.

### Scope

This state machine governs **project operational state**: where the project stands in its orchestration lifecycle.

Workflows have their own progression status — in progress, blocked, completed — within a project. Workflow status does not replace project state. Project state is the single authoritative operational position of the project as a whole. Workflow progression may *trigger* project state transitions but does not substitute for them.

Plugins may extend project state with domain-specific dimensions. Extensions must not violate the canonical states, transitions, or invariants defined here.

---

## States

A project occupies exactly one canonical state at any time.

### Lifecycle States

| State | Orchestration | Description |
|-------|---------------|-------------|
| **Created** | None | The project is defined with initial intent. Orchestration structure is not yet established. |
| **Initialized** | None | Core structure is in place: workflows, extensions, and initial configuration are established. |
| **Planning** | Structured | Workflows are active or being structured. Tasks are defined and dependencies evaluated. |
| **Ready** | Eligible | Required preconditions are satisfied. Tasks may become ready for execution. |
| **Executing** | In progress | Work is actively progressing. Tasks are ready, in flight, or being completed. |
| **Awaiting Approval** | Gated | A human approval checkpoint has been reached. Normal progression is frozen until a recorded decision. |
| **Blocked** | Halted | Involuntary obstruction. Orchestration cannot proceed safely. Cause is recorded and surfaced. |
| **Failed** | Halted | A required task or workflow failure prevents normal progression without remediation. |
| **Recovering** | Restricted | Remediation is in progress. Only recovery-scoped work may proceed until criteria are met. |

### Terminal States

| State | Orchestration | Description |
|-------|---------------|-------------|
| **Completed** | None | Project objectives are met or the project is intentionally closed. No active orchestration. |
| **Archived** | None | The project is retained for audit and reference only. No orchestration. Restoration requires governance. |

### State Diagram

```
                    ┌─────────────┐
                    │   Created   │
                    └──────┬──────┘
                           │ initialize
                           ▼
                    ┌─────────────┐
                    │ Initialized │
                    └──────┬──────┘
                           │ begin planning
                           ▼
                    ┌─────────────┐
         ┌─────────│  Planning   │◄────────┐
         │         └──────┬──────┘         │
         │                │ ready          │ replan
         │                ▼                │
         │         ┌─────────────┐         │
         │         │    Ready    │─────────┘
         │         └──────┬──────┘
         │                │ execute
         │                ▼
         │    ┌───────────────────────┐
         │    │      Executing        │◄──────────────┐
         │    └───┬────┬────┬────┬────┘               │
         │        │    │    │    │                    │
         │  gate  │    │    │    │ complete           │ resume
         │        │    │    │    ▼                    │
         │        │    │    │ ┌───────────┐           │
         │        │    │    │ │ Completed │──archive──► Archived
         │        │    │    │ └─────┬─────┘           │
         │        │    │    │       │ reopen          │
         │        │    │    │       └─────────────────┘
         │        ▼    ▼    ▼
         │   ┌────────┐ ┌────────┐ ┌────────┐
         │   │Awaiting│ │ Blocked│ │ Failed │
         │   │Approval│ └───┬────┘ └───┬────┘
         │   └───┬────┘     │          │
         │       │          │          │
         │       └──────────┼──────────┤
         │                  ▼          │
         │            ┌───────────┐    │
         └───────────►│ Recovering│◄───┘
                      └───────────┘
```

---

## Valid Transitions

Transitions are directed. Only the transitions listed below are valid unless explicitly extended through architecture review.

### From Created

| To | Trigger |
|----|---------|
| **Initialized** | Project structure is established: workflows, configuration, and extensions are registered. |

### From Initialized

| To | Trigger |
|----|---------|
| **Planning** | Recorded authorization to begin workflow structuring and planning. |

### From Planning

| To | Trigger |
|----|---------|
| **Ready** | Planning criteria satisfied; tasks are eligible to become ready. |
| **Blocked** | Obstruction prevents safe planning progression. |

### From Ready

| To | Trigger |
|----|---------|
| **Executing** | Work execution begins — tasks are ready and authorized to proceed. |
| **Planning** | Recorded decision to return to planning. |

### From Executing

| To | Trigger |
|----|---------|
| **Awaiting Approval** | A workflow reaches a human approval checkpoint. |
| **Blocked** | An unresolvable obstruction occurs. |
| **Failed** | A required task or workflow fails. |
| **Completed** | Project completion criteria are satisfied. |
| **Recovering** | Recorded authorization to enter remediation. |
| **Ready** | Execution pauses with work still eligible but not in flight. |

### From Awaiting Approval

| To | Trigger |
|----|---------|
| **Executing** | Recorded approval authorizes progression. |
| **Blocked** | Rejection, ambiguity, or obstruction prevents continuation. |
| **Failed** | Approval denied with failure outcome. |
| **Recovering** | Recorded authorization to remediate before resuming. |

### From Blocked

| To | Trigger |
|----|---------|
| **Recovering** | Recorded authorization to begin remediation. |
| **Executing** | Obstruction resolved without formal recovery phase. |
| **Ready** | Obstruction resolved; work eligible but not executing. |
| **Planning** | Recorded decision to replan from blockage. |
| **Failed** | Blockage declared unrecoverable. |
| **Archived** | Recorded decision to abandon and archive. |

### From Failed

| To | Trigger |
|----|---------|
| **Recovering** | Recorded authorization to remediate failure. |
| **Planning** | Recorded decision to replan after failure. |
| **Archived** | Recorded decision to close and archive. |

### From Recovering

| To | Trigger |
|----|---------|
| **Executing** | Recovery criteria met; execution resumes. |
| **Ready** | Recovery criteria met; work ready but not executing. |
| **Blocked** | Remediation fails or new obstruction arises. |
| **Failed** | Recovery fails. |

### From Completed

| To | Trigger |
|----|---------|
| **Archived** | Recorded decision to archive. |
| **Executing** | Recorded authorization to reopen the project. |

### From Archived

| To | Trigger |
|----|---------|
| **Initialized** | Recorded governance authorization to restore. Restoration re-enters at **Initialized**, not **Executing**. |

---

## Transition Rules

Every state transition must satisfy these rules.

### Authorization

Every transition has an authorized cause. Valid cause categories:

| Cause | Description |
|-------|-------------|
| **Human decision** | A recorded decision by a human with authority for the transition type. |
| **Task outcome** | A recorded task result mapped by workflow rules to a state transition. |
| **Automation** | An automation rule within policy bounds that declares this transition. |
| **Workflow rule** | A defined workflow transition that maps progression to project state change. |
| **System** | Bootstrap, initialization, or migration events. |

No transition may occur without a recorded cause from one of these categories.

### Preconditions

Before a transition is applied:

- The project must currently occupy the source state.
- All transition-specific preconditions must be satisfied.
- No invariant may be violated by the resulting state.
- Human approval checkpoints must have recorded decisions where required.

### Atomicity

A transition is applied atomically. A project is never in two states simultaneously. Partial transitions are forbidden.

### Recording

Every applied transition records:

- Source state and destination state
- Cause category and specific cause reference
- Timestamp of application
- Human authorizer, when applicable
- Rationale, when the transition is corrective or restorative

### Propagation

Workflow progression may *trigger* project state transitions through authorized workflow rules. Project state does not change implicitly without a recorded transition.

---

## Terminal States

**Completed** and **Archived** are terminal with respect to normal orchestration.

### Completed

- No tasks are dispatched.
- No workflows advance.
- State history remains fully accessible.

A project in **Completed** may transition to **Archived** or, with recorded human authorization, reopen to **Executing**.

### Archived

- No orchestration of any kind.
- Restoration requires governance authorization and re-enters at **Initialized**.

---

## Recovery States

**Recovering** is the canonical recovery state for in-flight remediation.

### Entering Recovering

From **Blocked**, **Awaiting Approval**, **Executing**, or **Failed** when remediation is authorized.

### Exiting Recovering

| Destination | Condition |
|-------------|-----------|
| **Executing** | Recovery criteria met; execution resumes. |
| **Ready** | Recovery criteria met; work ready but not executing. |
| **Blocked** | Remediation fails or stalls. |
| **Failed** | Recovery fails. |

---

## Blocked and Failed State Handling

**Blocked** is an involuntary halt — orchestration cannot proceed safely.

**Failed** is a declared failure state — required work did not succeed and progression requires remediation, replanning, or closure.

### Causes

| Cause Class | Typical State |
|-------------|---------------|
| Task failure | **Failed** or **Blocked** |
| Worker unavailability | **Blocked** |
| Ambiguity | **Blocked** |
| Approval rejection | **Blocked** or **Failed** |
| Unrecoverable failure | **Failed** |

### Blocked vs Failed

| Dimension | Blocked | Failed |
|-----------|---------|--------|
| Nature | Obstruction — may be transient | Outcome — work did not succeed |
| Resolution | Resolve obstruction | Remediate, replan, or archive |
| Normal path | Return to Ready or Executing | Return via Recovering or Planning |

---

## Human Approval Checkpoints

When a workflow reaches a gate requiring human judgment, the project transitions to **Awaiting Approval**.

While **Awaiting Approval**:

- Normal workflow progression is frozen.
- The required decision is recorded and surfaced.
- Automation does not bypass the checkpoint.
- No transition to **Executing** occurs without recorded approval.

Valid decisions: **Approve**, **Reject**, **Remediate** (to **Recovering**).

---

## State Invariants

1. A project occupies exactly one canonical state at any moment.
2. Every transition has a recorded cause.
3. Only valid transitions defined in this document may occur.
4. Historical state is never silently altered.
5. Human approval checkpoints cannot be bypassed.
6. Terminal states admit no orchestration without explicit restorative authorization.
7. **Executing** and **Recovering** are the primary states for active work tracking.
8. **Planning**, **Ready**, **Executing**, **Awaiting Approval**, and **Recovering** permit workflow orchestration activity.
9. Workflow progression triggers project state changes only through authorized workflow rules.
10. Plugin extensions must not violate these invariants.

---

## Orchestration Eligibility by State

| State | Track Workflows | Track Tasks | Dispatch Tasks | Human Action |
|-------|----------------|-------------|----------------|--------------|
| **Created** | No | No | No | Initialize |
| **Initialized** | Load only | No | No | Begin planning |
| **Planning** | Yes | Yes | Yes* | Per workflow |
| **Ready** | Yes | Yes | Yes* | Begin execution |
| **Executing** | Yes | Yes | Yes | Per gates |
| **Awaiting Approval** | Frozen | Review | No | Approve/reject |
| **Blocked** | Diagnosis | Diagnosis | No | Resolve |
| **Failed** | Remediation | Remediation | No | Remediate/replan |
| **Recovering** | Recovery-scoped | Recovery-scoped | Recovery-scoped | Per criteria |
| **Completed** | No | No | No | Archive or reopen |
| **Archived** | No | No | No | Restore |

\*From `planning` or `ready`, the runtime promotes the project to `executing` before assigning the first task (`ensure_executing`). Dispatch is blocked in terminal and gated states.

---

## Persistence

Runtime implementation persists:

| Artifact | Location | Purpose |
|----------|----------|---------|
| Current state | `.vedaws/state.toml` | Authoritative project state |
| Transition history | `.vedaws/transitions.jsonl` | Append-only audit log |
| Mirrored state | `.vedaws/project.toml` | Human-readable manifest mirror |

---

## Relationship to Other Documents

| Document | Relationship |
|----------|--------------|
| `002_CORE.md` | Defines State and Project lifecycle concepts. |
| `003_RUNTIME.md` | Runtime state management responsibilities. |
| `005_AUTOMATION.md` | `transition_state` automation action (implemented). |
| `007_PROJECT_MODEL.md` | On-disk project layout and `state.toml` authority. |
| `003_RUNTIME.md` / WorkflowEngine | Workflow activation and completion trigger state transitions. |

---

## TODO

- Define automation-authorized transitions in `005_AUTOMATION.md`. ✅ (`transition_state` action)
- Align acceptance checkpoint behavior with `008_ARTIFACTS.md` — domain plugins scaffold acceptance paths; formal checkpoint model deferred.
- `paused` project state — **not implemented at v0.5**; use `blocked` for halted projects (`002_CORE.md`). Dedicated `paused` semantics deferred.
- Add state machine visualization CLI — deferred (review technical debt).
