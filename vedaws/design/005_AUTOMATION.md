# Automation

**Version:** 0.5.0

**Status:** Active — v0.5 freeze (rule engine implemented Milestone 11)

## Purpose

The **Automation Engine** reacts to runtime **events** with data-driven **rules**. It is entirely domain-neutral — no knowledge of software, Unity, Git, or AI providers lives in the core.

```
Event → Condition (optional) → Action(s)
```

Plugins may **contribute rules**. The runtime **owns execution**.

---

## Rule Model

| Field | Description |
|-------|-------------|
| `id` | Unique rule identifier |
| `on_event` | Event type to listen for (`TaskCompleted`, …) |
| `if` / `conditions` | Optional payload matchers (all must match) |
| `then` / `actions` | One or more actions to execute |
| `enabled` | Per-rule enable flag |
| `description` | Human-readable summary |

Condition keys support aliases: `task` → `task_id`, `workflow` → `workflow_id`.

---

## Actions (v0.1)

| Action | Parameters | Description |
|--------|------------|-------------|
| `execute_worker` | `worker_id`, optional `task_ref` | Run a worker standalone or dispatch to a workflow task |
| `publish_event` | `event_type`, optional `payload` | Publish a new event (depth-limited) |
| `transition_state` | `state`, optional `reason`, `trigger` | Transition project lifecycle state |
| `workflow_step` | `task_ref`, `step` (`dispatch`, `complete`, `fail`), optional `worker_id` | Advance or dispatch a workflow task |
| `plugin_command` | `group`, `command`, optional `args` | Invoke a plugin CLI handler programmatically |

New action types can be added without changing domain plugins.

---

## Registration

### Project rules — `.vedaws/automation.toml`

```toml
[automation]
enabled = true

[[rules]]
id = "on-implement-complete"
description = "Check git after implement task"
on_event = "TaskCompleted"

[rules.if]
task_id = "implement"
workflow_id = "software"

[[rules.then]]
type = "execute_worker"
worker_id = "git.status"
```

### Plugin rules — SDK

```python
context.contribute_automation_rule(
    AutomationRule(
        id="software.implement-git-status",
        on_event=EventType.TASK_COMPLETED,
        conditions=RuleCondition.from_mapping({"task_id": "implement"}),
        actions=(RuleAction(type="execute_worker", params={"worker_id": "git.status"}),),
    )
)
```

Project rules override plugin rules with the same `id`.

Per-rule overrides:

```toml
[automation.overrides."software.implement-git-status"]
enabled = false
```

---

## Execution

1. `EventBus.publish()` dispatches synchronously
2. `AutomationEngine` receives subscribed event types
3. Enabled rules matching `on_event` are evaluated
4. Conditions checked against `event.payload`
5. Actions executed in order via `ActionExecutor`

**Guards:**

- `automation_depth` metadata limits nested `publish_event` chains
- Active rule chain detects re-entrant rule execution
- `doctor` validates rule registry, bindings, invalid actions, circular publish cycles

---

## CLI

| Command | Description |
|---------|-------------|
| `vedaws automation list` | List registered rules |
| `vedaws automation enable <id>` | Enable a rule (writes override) |
| `vedaws automation disable <id>` | Disable a rule |
| `vedaws automation run --rule <id>` | Manually execute a rule |
| `vedaws automation run --event <type> [--payload k=v]` | Run all matching rules for a synthetic event |

---

## Diagnostics

`vedaws doctor` includes an **automation** check:

- Rule registry populated
- Event bindings valid
- Unknown action types / invalid states flagged
- Circular `publish_event` triggers reported as warnings

---

## Relationship to Other Documents

| Document | Relationship |
|----------|--------------|
| `003_RUNTIME.md` | Bootstrap wires `AutomationEngine` after `AIService` |
| `010_PLUGINS.md` | `contribute_automation_rule` SDK |
| `006_STATE_MACHINE.md` | `transition_state` action |
| `004_WORKERS.md` | `execute_worker` action |
| `017_AI_PROVIDERS.md` | No `invoke_ai` action at v0.5; AI routing is separate from automation |

---

## v0.5 freeze boundary

| In scope (frozen) | Out of scope (deferred) |
|-------------------|-------------------------|
| Rule model (`on_event`, `if`, `then`) | `invoke_ai` automation action |
| Five action types (see Actions table) | Scheduling / background execution |
| Plugin + project rule registration | Rule priority and conflict resolution |
| CLI (`vedaws automation`) | Automation audit log persistence |
| Doctor automation checks | AI vendor integration in core |

Milestone 12 added the **AI Provider SDK** (`017_AI_PROVIDERS.md`). The automation engine remains domain-neutral and does **not** call `AIService` directly at v0.5.

---

## Future

- `invoke_ai` or plugin-local actions invoking `AIService` (after M13 worker binding)
- Scheduling and background execution (deferred)
- Rule priority and conflict resolution
- Automation audit log

---

## Non-goals (v0.5)

- **Automation engine invoking vendor AI** — no Gemini/OpenAI/Claude/Cursor/MCP in core automation actions
- **Scheduling, background workers, distributed execution**
- Vendor SDK imports in `runtime/vedaws/automation/`
