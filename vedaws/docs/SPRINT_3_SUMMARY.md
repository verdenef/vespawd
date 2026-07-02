# Sprint 3 Summary — Project Lifecycle

**Status:** Complete  
**Version:** 0.1.0

Sprint 3 implements the canonical project lifecycle state machine — Vedaws' first real orchestration capability. Project state is modeled, persisted, validated, and transitioned. Workers do not execute tasks.

---

## 1. Repository Tree

```
vedaws/
├── pyproject.toml
├── VEDAWS_BOOTSTRAP.md
├── .gitignore
│
├── design/                         # Architecture documents (000–016)
│
├── runtime/vedaws/                 # Python package
│   ├── __init__.py
│   ├── __main__.py
│   │
│   ├── cli/
│   │   ├── app.py
│   │   └── commands.py             # + vedaws state, state history, state transition
│   │
│   ├── config/
│   │   ├── defaults.py
│   │   ├── loader.py
│   │   ├── paths.py                # + PROJECT_STATE_FILE, PROJECT_HISTORY_FILE
│   │   └── schema.py
│   │
│   ├── doctor/
│   │   ├── checks.py               # + project state validation
│   │   └── model.py
│   │
│   ├── logging/
│   ├── plugins/                    # Sprint 1
│   ├── project/
│   │   ├── detector.py             # loads StateEngine, syncs manifest
│   │   ├── init.py                 # creates state.toml + initial history
│   │   ├── model.py                # ProjectContext + state_engine
│   │   └── state/                  # Sprint 3 — State machine
│   │       ├── states.py           # ProjectState enum
│   │       ├── triggers.py         # TransitionTrigger enum
│   │       ├── transitions.py      # VALID_TRANSITIONS map
│   │       ├── models.py           # TransitionRecord, errors
│   │       ├── persistence.py      # state.toml + transitions.jsonl
│   │       ├── engine.py           # StateEngine + listeners
│   │       └── reporter.py         # CLI formatting
│   │
│   ├── runtime/
│   │   ├── bootstrap.py            # restores + validates project state
│   │   ├── context.py
│   │   └── status.py
│   │
│   ├── status/
│   │   └── reporter.py             # shows canonical project state
│   │
│   └── workers/                    # Sprint 2
│
├── workers/                        # Bundled worker manifests
├── plugins/hello/                    # Bundled plugin manifest
│
├── tests/
│   ├── test_bootstrap.py
│   ├── test_cli.py                 # + state command tests
│   ├── test_config.py
│   ├── test_plugins.py
│   ├── test_state.py               # NEW
│   └── test_workers.py
│
├── examples/sprint1-demo/.vedaws/
└── docs/
    ├── SPRINT_2_WORKER_REGISTRY.md
    └── SPRINT_3_SUMMARY.md
```

### Per-project files (`.vedaws/`)

```
.vedaws/
├── project.toml          # name + mirrored state field
├── config.toml           # project configuration
├── state.toml            # authoritative current state
└── transitions.jsonl     # append-only transition history
```

---

## 2. Architecture Summary

```
CLI (vedaws state | state history | state transition)
         │
         ▼
Runtime Bootstrap
    ├── load_config()
    ├── discover_plugins() → PluginRegistry
    ├── discover_workers() → WorkerRegistry
    └── detect_project()
            ├── StateEngine.load(.vedaws/)
            ├── validate current state
            ├── restore transition history
            └── ProjectContext (name + state_engine)

StateEngine.transition(target, trigger, reason)
    ├── check VALID_TRANSITIONS
    ├── persist state.toml
    ├── append transitions.jsonl
    └── notify TransitionListener(s)    ← future event bus hook
```

### Canonical States

| State | Value | Notes |
|-------|-------|-------|
| Created | `created` | Initial state after `vedaws init` |
| Initialized | `initialized` | Structure established |
| Planning | `planning` | Planning phase |
| Ready | `ready` | Ready to execute |
| Executing | `executing` | Active orchestration |
| Awaiting Approval | `awaiting_approval` | Human gate |
| Completed | `completed` | Terminal |
| Blocked | `blocked` | Involuntary halt |
| Failed | `failed` | Failure state |
| Recovering | `recovering` | Remediation in progress |
| Archived | `archived` | Terminal, audit-only |

Invalid transitions are rejected with `InvalidTransitionError`. Every valid transition is recorded before the new state takes effect.

### Transition Triggers

| Trigger | Value |
|---------|-------|
| Human decision | `human_decision` |
| Task outcome | `task_outcome` |
| Automation | `automation` |
| Workflow rule | `workflow_rule` |
| System | `system` |

### Key Design Decisions

| Principle | Implementation |
|-----------|----------------|
| Single authoritative state | `state.toml` is source of truth; `project.toml` is mirrored |
| Enforced transitions | `VALID_TRANSITIONS` map; no silent state changes |
| Full audit trail | Append-only `transitions.jsonl` with timestamp, trigger, reason |
| Event-ready | `StateEngine.subscribe()` listener hooks; no event bus yet |
| Runtime validation | Bootstrap calls `engine.validate()` on every project load |
| Legacy migration | Projects without `state.toml` are migrated from `project.toml` |

### Design Note

Sprint 3 states (`planning`, `ready`, `executing`, `failed`) extend the design doc `006_STATE_MACHINE.md` model (`active`, `paused`). Reconciliation with the design document is a future architecture task.

---

## 3. Public APIs and Interfaces Introduced

### CLI

| Command | Purpose |
|---------|---------|
| `vedaws state [-C path]` | Show current state, allowed next states, transition count |
| `vedaws state history [-C path]` | Show full transition history with timestamps |
| `vedaws state transition <to> [-C path] [--reason] [--trigger]` | Apply a valid state transition |

`vedaws status` and `vedaws doctor` were extended to report and validate project state.

---

### `ProjectState` (`vedaws.project.state.states`)

Enum of all canonical lifecycle states.

| Member | Description |
|--------|-------------|
| `parse(value)` | Parse string to `ProjectState` or `None` |
| `is_terminal` | `True` for `completed`, `archived` |
| `allows_orchestration` | `True` for planning, ready, executing, awaiting_approval, recovering |

---

### `TransitionTrigger` (`vedaws.project.state.triggers`)

Enum of authorized transition cause categories per `006_STATE_MACHINE.md`.

| Value | Meaning |
|-------|---------|
| `human_decision` | Recorded human authorization |
| `task_outcome` | Task result mapped to transition |
| `automation` | Automation rule within policy |
| `workflow_rule` | Workflow-defined transition |
| `system` | Bootstrap / initialization |

---

### `TransitionRecord` (`vedaws.project.state.models`)

Immutable record of one state change.

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `str` | ISO 8601 UTC |
| `previous_state` | `str` | State before transition |
| `new_state` | `str` | State after transition |
| `trigger` | `str` | Cause category |
| `reason` | `str \| None` | Optional human-readable rationale |

Factory: `TransitionRecord.create(previous, new, trigger, reason?)`

---

### `StateEngine` (`vedaws.project.state.engine`)

Core state machine. All future orchestration reads and writes project state through this interface.

| Method / Property | Purpose |
|-------------------|---------|
| `load(project_dir, legacy_state?)` | Restore state and history from disk |
| `current` | Current `ProjectState` |
| `history` | List of `TransitionRecord` |
| `validate()` | Raise `StateValidationError` if state is invalid |
| `allowed_transitions()` | Valid target states from current |
| `can_transition_to(target)` | Boolean transition check |
| `transition(target, trigger, reason?)` | Apply transition, persist, notify listeners |
| `subscribe(listener)` | Register `TransitionListener` callback |

`TransitionListener = Callable[[TransitionRecord], None]`

---

### Transition Rules (`vedaws.project.state.transitions`)

| Function | Purpose |
|----------|---------|
| `is_valid_transition(from, to)` | Returns `True` if transition is permitted |
| `allowed_targets(from)` | Returns `frozenset[ProjectState]` of valid targets |
| `VALID_TRANSITIONS` | Full transition map |

---

### Persistence (`vedaws.project.state.persistence`)

| Function | Purpose |
|----------|---------|
| `load_current_state(project_dir)` | Read authoritative state from `state.toml` |
| `save_current_state(project_dir, state)` | Write `state.toml` |
| `load_history(project_dir)` | Read all records from `transitions.jsonl` |
| `append_history(project_dir, record)` | Append one transition record |
| `initialize_state(project_dir, state)` | Create initial state files |

Constants: `STATE_FILE_NAME`, `HISTORY_FILE_NAME`

---

### Exceptions

| Exception | When raised |
|-----------|-------------|
| `InvalidTransitionError` | Transition not in `VALID_TRANSITIONS` |
| `StateValidationError` | Missing or corrupt persisted state |

---

### `ProjectContext` (updated)

| Field / Property | Type | Description |
|------------------|------|-------------|
| `root` | `Path` | Project workspace root |
| `name` | `str` | Project name |
| `state_engine` | `StateEngine` | Lifecycle engine instance |
| `state` | `ProjectState` | Current state (via engine) |
| `state_name` | `str` | Current state as string |

---

## 4. Directory Structure Overview

| Directory / File | Role |
|------------------|------|
| `runtime/vedaws/project/state/` | State machine — engine, rules, persistence |
| `runtime/vedaws/project/` | Project init, detection, context model |
| `runtime/vedaws/runtime/` | Bootstrap loads and validates state on startup |
| `runtime/vedaws/cli/` | `vedaws state` command group |
| `runtime/vedaws/doctor/` | `project state` health check |
| `runtime/vedaws/status/` | Displays canonical state in `vedaws status` |
| `.vedaws/state.toml` | Authoritative current state (per project) |
| `.vedaws/transitions.jsonl` | Append-only transition audit log (per project) |
| `.vedaws/project.toml` | Project manifest; state field mirrored from `state.toml` |
| `design/006_STATE_MACHINE.md` | Design reference (partial alignment) |
| `tests/test_state.py` | State engine unit tests |

---

## Current State

| Layer | Status |
|-------|--------|
| State machine | 11 states, enforced transitions |
| Persistence | `state.toml` + `transitions.jsonl` |
| Transition history | Timestamp, previous/new state, trigger, reason |
| Runtime integration | Load, validate, expose on `RuntimeContext` |
| CLI | `state`, `state history`, `state transition` |
| Event bus | Not implemented; `subscribe()` hooks ready |
| Worker execution | Not implemented (by design) |
| Automation | Not implemented (by design) |

**27 tests passing.**

---

## Suggested Next Sprint

**Sprint 4: Workflow Definitions**

1. Define workflow schema aligned with `002_CORE.md`
2. Load workflows from `.vedaws/` or plugins
3. Map workflow progression to state transitions via `TransitionTrigger.WORKFLOW_RULE`
4. Gate orchestration actions by `ProjectState.allows_orchestration`
