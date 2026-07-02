# Vespawd Bridge Implementation Specification

**Status:** Implementation specification (design only — no source code)  
**Audience:** Implementers and AI coding agents building the Bridge in `main/bridge/`  
**Canonical references:** [VESPAWD_ARCHITECTURE.md](VESPAWD_ARCHITECTURE.md), [VESPAWD_BRIDGE_SPEC.md](VESPAWD_BRIDGE_SPEC.md), [VESPAWD_EXECUTOR_SPEC.md](VESPAWD_EXECUTOR_SPEC.md), [PLANNER_SPEC.md](PLANNER_SPEC.md)  
**Constraint:** MUST NOT modify `paws022/` or `vedaws/`. Implementation MUST remain invocable by any Executor without IDE coupling.

---

## Normative language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in RFC 2119.

---

## 1. Overall implementation architecture

The Bridge implementation MUST be structured as a **single deployable unit** under `main/bridge/` with **internal modules** and one **public entry surface** callable by the Executor (subprocess CLI, library call, or equivalent — implementation choice).

### 1.1 Architecture diagram

```
                    ┌─────────────────────────────────────┐
                    │         Public API (entry)          │
                    │  invoke(operation, context, input)  │
                    └──────────────────┬──────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │       Operation dispatcher          │
                    │  prepare → route → finalize result  │
                    └──────────────────┬──────────────────┘
           ┌───────────────────────────┼───────────────────────────┐
           │                           │                           │
┌──────────▼──────────┐   ┌───────────▼──────────┐   ┌───────────▼──────────┐
│  Manifest loader    │   │  Validation engine   │   │  Recovery engine     │
│  + path resolver    │   │  (gates, layout)     │   │  (idempotent retry)  │
└──────────┬──────────┘   └───────────┬──────────┘   └───────────┬──────────┘
           │                           │                           │
           └───────────────────────────┼───────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │          CLI adapter                │
                    │  vedaws subprocess orchestration    │
                    └──────────────────┬──────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │       Projection engine             │
                    │  Vedaws snapshot → PAWS files       │
                    └─────────────────────────────────────┘
```

### 1.2 Internal modules

| Module | Responsibility | MUST NOT |
|--------|----------------|----------|
| **Public API** | Single entry; accept operation name + `BridgeContext` + operation input; return `BridgeResult` | Contain operation business logic inline |
| **Operation dispatcher** | Shared prepare/finalize; route to operation handlers; enforce sync order side effects | Invoke Vedaws directly without CLI adapter |
| **Manifest loader** | Parse `manifest.toml`; validate schema; resolve relative paths | Guess missing manifest keys |
| **Path resolver** | Compute workspace, POS, Vedaws, userspace absolute paths from manifest + `project_context.md` | Write PAWS memory except projections |
| **CLI adapter** | Build argv; run subprocess; map exit codes; enforce allowlist | Execute non-allowlisted Vedaws commands |
| **Projection engine** | Generate `status.md`; enrich `current_task.md` Notes; optional HANDOFF mirror | Overwrite Goal/Criteria/backlog |
| **Validation engine** | Doctor, design gate, eligibility, layout, version checks | Plan scope or implement code |
| **Recovery engine** | Classify failures; recommend retries; idempotent bootstrap/sync | Auto-destruct `.vedaws/` without human flag |
| **Logging** | Structured logs with correlation id per invocation | Log secrets or full HANDOFF prose |

### 1.3 Public API

The public API MUST expose exactly these operations (names normative):

| Operation | Input type | Output |
|-----------|------------|--------|
| `bootstrap` | `BootstrapInput` | `BridgeResult` |
| `ingest_master_prompt` | `MasterPromptIngest` | `BridgeResult` |
| `sync_status` | `SyncInput` | `BridgeResult` |
| `pre_implement_check` | `ImplementGateInput` | `BridgeResult` |
| `post_implement` | `PostImplementInput` | `BridgeResult` |
| `post_phase_complete` | `PhaseCompleteInput` | `BridgeResult` |
| `pre_documenter` | `DocumenterGateInput` | `BridgeResult` |

**Entry contract:**

- **Input:** `BridgeContext` (workspace root, optional correlation id, optional session overrides) + operation-specific payload.
- **Output:** `BridgeResult` (§9).
- **Concurrency:** Implementations MUST treat each invocation as independent; MUST NOT assume in-process global mutable state across invocations without explicit session store.
- **Invocation transport:** Implementations MAY expose a thin CLI wrapper (`bridge invoke <operation> …`) that serializes JSON input/output for Executor subprocess use.

### 1.4 Operation dispatcher

The dispatcher MUST execute this sequence for every operation:

```
1. ASSIGN correlation_id (from context or generate)
2. LOG operation_start
3. LOAD manifest via manifest loader → ManifestModel
4. RESOLVE paths via path resolver → ResolvedPaths
5. VALIDATE layout + version (validation engine, layout + version only)
6. VERIFY vedaws CLI presence (cli_adapter.ping)
7. ROUTE to operation handler
8. COLLECT CLI results + validation results
9. RUN projection engine if handler requests
10. BUILD BridgeResult
11. LOG operation_end (duration, ok, codes)
12. RETURN BridgeResult
```

If step 3–6 fails, dispatcher MUST NOT run operation handler; MUST return failure `BridgeResult` immediately.

### 1.5 Manifest loader

MUST read `main/bridge/manifest.toml` relative to Vedaws project root (`main/`). MUST produce immutable `ManifestModel` for the invocation lifetime.

### 1.6 CLI adapter

MUST be the **only** module that spawns Vedaws subprocesses. MUST enforce command allowlist per [VESPAWD_BRIDGE_SPEC.md](VESPAWD_BRIDGE_SPEC.md) §7.1.

### 1.7 Projection engine

MUST implement Vedaws → PAWS rules in [VESPAWD_BRIDGE_SPEC.md](VESPAWD_BRIDGE_SPEC.md) §6. MUST be callable independently via `sync_status` and as sub-step of other operations.

### 1.8 Validation engine

MUST expose composable validators invoked by operation handlers and dispatcher prepare phase.

### 1.9 Recovery engine

MUST map failure codes to recovery recommendations (§9.2). MAY implement automatic single-retry for transient CLI failures per §6.4.

---

## 2. Directory structure

Complete normative tree for `main/bridge/`:

```
main/bridge/
├── manifest.toml              # Runtime config: paths, phase map, versions
├── README.md                  # Human: how Executor invokes Bridge
├── spec/                      # Frozen copies or pointers to Vespawd specs (optional)
│   └── VERSION                # Bridge implementation semver
├── schema/                    # Machine-readable contracts (optional)
│   ├── manifest.schema.toml   # Manifest validation rules
│   ├── bridge_result.schema   # BridgeResult field contract
│   └── operations.schema      # Per-operation input shapes
├── bin/                       # Entry executable or launcher (implementation)
│   └── bridge                 # Public CLI entry: invoke operations
├── lib/                       # Implementation root (name arbitrary)
│   ├── api/                   # Public API + BridgeContext/BridgeResult types
│   ├── dispatcher/            # Operation dispatcher + handler registry
│   ├── manifest/              # Manifest loader + path resolver
│   ├── cli/                   # CLI adapter (allowlist, retry, timeout)
│   ├── projection/            # status.md, Notes enrichment, HANDOFF mirror
│   ├── validation/            # Doctor, design, eligibility, layout, version
│   ├── recovery/              # Failure classification + retry policy
│   ├── operations/            # One handler per operation
│   │   ├── bootstrap
│   │   ├── ingest_master_prompt
│   │   ├── sync_status
│   │   ├── pre_implement_check
│   │   ├── post_implement
│   │   ├── post_phase_complete
│   │   └── pre_documenter
│   └── logging/               # Correlation, levels, timing
├── hooks/                     # Extension points (§12); OPTIONAL v1 stubs
│   ├── README.md              # Hook contract documentation
│   └── examples/              # No-op hook samples
├── sync/                      # Reserved: projection templates / fixtures
│   └── status.template.md     # status.md skeleton
└── tests/                     # Test suites (§11)
    ├── unit/
    ├── integration/
    ├── recovery/
    └── fixtures/              # Mock CLI output, sample manifests
```

### 2.1 File purposes

| Path | Purpose |
|------|---------|
| `manifest.toml` | Authoritative Bridge configuration; committed per project |
| `README.md` | Executor integration instructions; operation list |
| `spec/VERSION` | Implementation version for compatibility checks |
| `schema/*` | Optional validation artifacts for manifest and payloads |
| `bin/bridge` | Executor-invoked entry point |
| `lib/api/` | Stable outward contract; minimize breaking changes |
| `lib/dispatcher/` | Central routing and shared prepare/finalize |
| `lib/manifest/` | Parse, validate, resolve paths |
| `lib/cli/` | Vedaws subprocess isolation |
| `lib/projection/` | PAWS file generation rules |
| `lib/validation/` | All gate checks |
| `lib/recovery/` | Error → recommendation mapping |
| `lib/operations/*` | Operation-specific sequences (§4) |
| `lib/logging/` | Observability |
| `hooks/` | Future user extensions without forking core |
| `sync/status.template.md` | Projection engine template source |
| `tests/` | Automated verification per §11 |

Implementations MAY flatten `lib/` but MUST preserve logical module boundaries.

---

## 3. Internal interfaces

### 3.1 BridgeContext (input envelope)

Every operation MUST receive:

| Field | Required | Description |
|-------|----------|-------------|
| `workspace_root` | YES | Absolute path to Vespawd workspace root |
| `correlation_id` | NO | Executor-supplied id; generated if absent |
| `session_overrides` | NO | Map: `skip_design`, `design_later`, `force_phase`, `human_approved_destructive_recovery` |
| `executor_metadata` | NO | Opaque bag (e.g. changed_paths for post_implement) |

### 3.2 ResolvedPaths (internal)

Produced by path resolver; passed to handlers:

| Field | Description |
|-------|-------------|
| `pos_root` | PAWS root directory |
| `vedaws_project_root` | Directory containing `.vedaws/` |
| `userspace_root` | Application source root (`main/src/` or `src/`) |
| `manifest_path` | Absolute path to manifest.toml |
| `current_task_path` | PAWS current_task.md |
| `status_path` | PAWS status.md |
| `handoff_path` | PAWS HANDOFF path |
| `design_gate_path` | DESIGN.md path |
| `project_context_path` | project_context.md |
| `layout` | `sidecar` \| `integrated` |

### 3.3 VedawsSnapshot (internal)

CLI adapter MUST normalize command output into:

| Field | Source commands |
|-------|-----------------|
| `project_state` | `vedaws status`, `vedaws state` |
| `active_workflow_id` | `vedaws workflow show` |
| `active_task_id` | `vedaws workflow show` |
| `task_states` | `vedaws workflow show`, `vedaws tasks show` |
| `doctor_ok` | `vedaws doctor` |
| `doctor_summary` | `vedaws doctor` stdout/stderr |
| `artifacts_report` | `vedaws software artifacts` |
| `raw_outputs` | Per-command stdout/stderr for diagnostics |

### 3.4 BridgeResult (output envelope)

Normative fields — implementations MUST include all:

| Field | Type | Description |
|-------|------|-------------|
| `ok` | boolean | `true` iff operation succeeded per operation rules |
| `operation` | string | Operation name |
| `correlation_id` | string | Echo or generated |
| `codes` | string[] | Machine failure/warning codes (§9.1) |
| `blockers` | string[] | Human-readable blockers for Executor |
| `warnings` | string[] | Non-fatal messages |
| `vedaws_task_id` | string | e.g. `software.implement` |
| `project_state` | string | Vedaws lifecycle state |
| `doctor_summary` | string | Truncated doctor output |
| `files_touched` | string[] | Relative paths written |
| `recovery` | RecoveryHint[] | §9.2 |
| `duration_ms` | number | Wall time |
| `vedaws_commands_run` | string[] | Audit trail of argv |

### 3.5 Data flow (normative)

```
Executor
  → BridgeContext + OperationInput
  → dispatcher.prepare (manifest, paths, cli ping)
  → operation.handler (validation, cli, projection)
  → BridgeResult
  → Executor interprets ok/codes/blockers
```

**PAWS writes:**

| Writer | Files |
|--------|-------|
| Executor (before ingest) | project_context, current_task, backlog |
| Bridge projection engine | status.md, Notes enrichment |
| Executor (after) | HANDOFF, userspace |

Bridge MUST NOT write backlog or project_context.

### 3.6 Error propagation

1. CLI adapter returns `CliResult { exit_code, stdout, stderr, timed_out }`.
2. Validation returns `ValidationResult { passed, codes, messages }`.
3. Handler sets `BridgeResult.ok = false` if any **blocking** code present.
4. Warnings MUST NOT alone set `ok = false` unless operation defines otherwise.
5. Uncaught internal errors MUST map to `internal_error` with `ok = false`; MUST NOT crash without `BridgeResult`.

---

## 4. Operation implementation

Shared prepare (all operations): dispatcher steps 1–6 (§1.4).

---

### 4.1 `bootstrap`

**Purpose:** Ensure Vedaws project and software workflow exist.

**Preconditions:** Manifest loaded; paths resolved.

**Sequence:**

| Step | Action |
|------|--------|
| 1 | `validation.layout` |
| 2 | `validation.version` (warn on mismatch) |
| 3 | If `.vedaws/project.toml` missing → `cli.init_software_template(name from project_context)` |
| 4 | `cli.workflow_show` → if workflow inactive → `cli.workflow_activate(software)` |
| 5 | `cli.doctor` |
| 6 | If state is `created` → `cli.state_transition(initialized)` when eligible |
| 7 | `projection.sync_status` (inline or call sync_status handler) |
| 8 | Build `BridgeResult` |

**Validations:** layout, version; doctor hard fail blocks `ok`.

**CLI calls:** `init`, `workflow show`, `workflow activate`, `doctor`, optional `state transition initialized`.

**Projections:** `status.md`; optional Notes if `current_task.md` exists.

**Failure handling:**

| Condition | Code | ok |
|-----------|------|-----|
| vedaws missing | `vedaws_missing` | false |
| init fails | `bootstrap_failed` | false |
| doctor hard fail | `doctor_blocked` | false |
| partial .vedaws | retry idempotent step 3–4 | — |

**Returned BridgeResult:** `ok=true` iff doctor passes and workflow active.

**Idempotency:** MUST be safe to call multiple times.

---

### 4.2 `ingest_master_prompt`

**Purpose:** Align Vedaws with parsed Master Prompt after Executor PAWS writes.

**Preconditions:** `current_task.md`, `backlog.md`, `project_context.md` already updated by Executor.

**Input (`MasterPromptIngest`):**

| Field | Required |
|-------|----------|
| `current_task.goal` | YES |
| `current_task.constraints` | NO |
| `current_task.acceptance_criteria` | YES |
| `current_task.notes` | NO |
| `project_context.product_name` | NO |
| `phase_hint` | NO |

**Sequence:**

| Step | Action |
|------|--------|
| 1 | `bootstrap` if `.vedaws/` missing (inline or delegate) |
| 2 | `phase_map.resolve(goal, notes, phase_hint)` → `vedaws_task_id` |
| 3 | `cli.workflow_show` |
| 4 | `cli.status` |
| 5 | If eligible → `cli.state_transition(planning)` or `executing` |
| 6 | `projection.enrich_notes(vedaws_task_id, project_state)` |
| 7 | `sync_status` (full handler or inline) |
| 8 | Build `BridgeResult` |

**Validations:** layout; phase map (warn `phase_map_miss` if fallback keyword match).

**CLI calls:** `workflow show`, `status`, optional `state transition`.

**Projections:** Notes enrichment; `status.md`.

**Failure handling:**

| Condition | Code | ok |
|-----------|------|-----|
| unmapped phase | `phase_map_miss` | true with warning |
| transition denied | `state_transition_denied` | false |
| bootstrap fails | propagate | false |

**Returned BridgeResult:** MUST include `vedaws_task_id`.

**MUST NOT** run `vedaws run` by default on ingest.

---

### 4.3 `sync_status`

**Purpose:** Project Vedaws snapshot to PAWS `status.md`.

**Sequence:**

| Step | Action |
|------|--------|
| 1 | If vedaws missing → write offline `status.md`; return `vedaws_missing` |
| 2 | `cli.status` + `cli.workflow_show` |
| 3 | Read `current_task.md` Status → App field |
| 4 | Read HANDOFF footer → Handoff fresh/stale |
| 5 | Read DESIGN.md status → Design gate field |
| 6 | `projection.write_status(snapshot, inputs)` |
| 7 | Optional `projection.enrich_notes` sync timestamp |
| 8 | Build `BridgeResult` |

**Validations:** none blocking except manifest/paths.

**CLI calls:** `status`, `workflow show`.

**Projections:** full `status.md` rewrite per template (§7.1).

**Failure handling:** vedaws offline → `orchestration_offline`, `ok=true`, preserve prior Phase if parse fails.

**Returned BridgeResult:** `files_touched` includes `status_path`.

**Idempotency:** MUST be safe to call repeatedly.

---

### 4.4 `pre_implement_check`

**Purpose:** Gate before userspace edits.

**Input (`ImplementGateInput`):**

| Field | Required |
|-------|----------|
| `current_task` | YES |
| `skip_design` | NO |
| `design_later` | NO |

**Sequence:**

| Step | Action |
|------|--------|
| 1 | `validation.layout` |
| 2 | `validation.manifest_integrity` |
| 3 | `cli.doctor` → `validation.doctor` |
| 4 | `validation.design_gate(current_task, overrides)` |
| 5 | `cli.workflow_show` + `validation.workflow_eligibility` |
| 6 | `validation.task_alignment(current_task, snapshot)` |
| 7 | Aggregate blocking codes |
| 8 | Build `BridgeResult` (`ok=false` if any blocker) |

**Validations:** all §8 modules applicable.

**CLI calls:** `doctor`, `workflow show`, `status` (if needed).

**Projections:** none required; MAY append blockers to Notes via `enrich_notes`.

**Failure handling:** each validation failure adds code + blocker message.

**Returned BridgeResult:** `ok=true` only if zero blocking codes.

---

### 4.5 `post_implement`

**Purpose:** Run automation dispatch without closing phase.

**Input (`PostImplementInput`):**

| Field | Required |
|-------|----------|
| `vedaws_task_id` | YES |
| `changed_paths` | NO |

**Sequence:**

| Step | Action |
|------|--------|
| 1 | `cli.run` with bounded iteration cap (default 1–3, configurable in manifest) |
| 2 | Capture worker/automation summary from stdout |
| 3 | Build `BridgeResult` with warnings on worker failure |

**Validations:** OPTIONAL doctor soft check.

**CLI calls:** `run` only.

**Projections:** none.

**Failure handling:** worker hard fail → warning unless task failed in Vedaws.

**Returned BridgeResult:** `ok=true` unless configured strict mode in manifest.

---

### 4.6 `post_phase_complete`

**Purpose:** Mark Vedaws task complete; sync; optional human gate state.

**Input (`PhaseCompleteInput`):**

| Field | Required |
|-------|----------|
| `vedaws_task_id` | YES |
| `outcome` | YES (`completed` \| `failed` \| `blocked`) |
| `reason` | NO |
| `human_gate` | NO (default true between planner phases) |

**Sequence:**

| Step | Action |
|------|--------|
| 1 | If outcome `completed` → `cli.tasks_complete(vedaws_task_id)` |
| 2 | If outcome `failed` → `cli.tasks_fail` if available else warning |
| 3 | `cli.run` (automation) |
| 4 | If `human_gate` → `cli.state_transition(awaiting_approval)` when eligible |
| 5 | `sync_status` |
| 6 | Build `BridgeResult` |

**Validations:** task exists in workflow; dependencies satisfied.

**CLI calls:** `tasks complete`, optional `tasks fail`, `run`, `state transition`, then sync commands.

**Projections:** via `sync_status`.

**Failure handling:** `task_complete_denied` if CLI rejects completion.

**Returned BridgeResult:** updated `project_state`, `files_touched`.

---

### 4.7 `pre_documenter`

**Purpose:** Handoff artifact gate.

**Sequence:**

| Step | Action |
|------|--------|
| 1 | `cli.doctor` |
| 2 | `cli.software_artifacts` |
| 3 | `validation.artifacts(missing list)` |
| 4 | Read HANDOFF freshness |
| 5 | If artifacts ok and handoff phase → `cli.tasks_complete(software.handoff)` |
| 6 | OPTIONAL `projection.mirror_handoff` to `main/docs/handoff/HANDOFF.md` (copy only) |
| 7 | `sync_status` |
| 8 | Build `BridgeResult` |

**Validations:** doctor, artifacts, HANDOFF stale warning.

**CLI calls:** `doctor`, `software artifacts`, optional `tasks complete software.handoff`.

**Projections:** `status.md`; optional HANDOFF mirror.

**Failure handling:** `artifacts_missing` → `ok=false` with path list in blockers.

**Returned BridgeResult:** artifact checklist in `warnings` or `blockers`.

---

## 5. Manifest parser

### 5.1 Loading order

1. Resolve `manifest_path` = `<vedaws_project_root>/bridge/manifest.toml`.
2. If missing → fail `missing_manifest`.
3. Parse TOML into `ManifestModel`.
4. Apply defaults from built-in Vespawd sidecar profile ONLY if `manifest.defaults = "vespawd-sidecar-v1"` explicit flag; otherwise fail on missing required keys.
5. Merge `[phase_map]` with built-in default phase table (§4.2 of Bridge Spec) — manifest entries override defaults.
6. Pass to `validation.manifest_schema`.

### 5.2 Validation

Manifest MUST contain:

| Section | Required keys |
|---------|---------------|
| `[vespawd]` | `version` |
| `[pos]` | `root`, `current_task`, `handoff`, `design_gate` |
| `[vedaws]` | `project_root`, `workflow_id`, `cli` |
| `[phase_map]` | OPTIONAL; at least one mapping if present |

Path validation:

- All paths MUST resolve relative to `vedaws_project_root` or `workspace_root` per manifest rule field.
- Resolved paths MUST exist for POS root and `tasks/` after bootstrap.
- `layout` MUST match `project_context.md` Mode when both present.

### 5.3 Compatibility checking

| Check | Behavior |
|-------|----------|
| `vespawd.version` vs implementation `spec/VERSION` | Major mismatch → `version_mismatch` hard fail; minor → warning |
| `vedaws.workflow_id` | MUST be `software` for v1 |
| Vedaws architecture | Implementation SHOULD declare supported Vedaws baseline `0.5.0` in manifest `[compat]` |

---

## 6. CLI adapter

### 6.1 Command construction

- Executable: resolved from `manifest.vedaws.cli` (path to vedaws install) or `vedaws` on PATH.
- Every command MUST include `--path <vedaws_project_root_abs>`.
- Arguments MUST match allowlist templates (§7.1 Bridge Spec).
- Implementations MUST log full argv in `vedaws_commands_run` audit field.

### 6.2 stdout/stderr handling

| Rule | Requirement |
|------|-------------|
| Capture | MUST capture both streams |
| Encoding | MUST use UTF-8 |
| Truncation | `doctor_summary` MUST truncate to configurable max (default 2000 chars) |
| Parsing | Prefer structured CLI output when available; else heuristic line parse |
| Secrets | MUST NOT log env vars or credential-bearing lines |

### 6.3 Exit code mapping

| Exit code | Meaning | Default mapping |
|-----------|---------|-----------------|
| 0 | Success | `cli_ok` |
| 1 | General failure | `cli_failed` |
| 2+ | Tool-specific | map per command table in implementation docs |
| timeout | No exit | `cli_timeout` |
| spawn error | Cannot run | `vedaws_missing` or `cli_spawn_error` |

Doctor: non-zero MAY be `doctor_blocked` for `pre_implement_check`; MAY be warning elsewhere.

### 6.4 Retry policy

| Condition | Retries | Backoff |
|-----------|---------|---------|
| `cli_timeout` | 1 | immediate |
| Transient spawn error | 2 | 100ms, 500ms |
| doctor fail | 0 | — |
| task complete denied | 0 | — |

Retries MUST be logged with `recovery.retry` code.

### 6.5 Timeout behavior

| Command class | Default timeout |
|---------------|-----------------|
| `version` | 10s |
| `status`, `workflow show`, `state` | 30s |
| `doctor` | 120s |
| `init` | 180s |
| `run` | 300s (manifest override) |

On timeout: kill subprocess; return `cli_timeout`; MUST NOT leave orphan processes.

---

## 7. Projection engine

### 7.1 `status.md` generation

- MUST overwrite entire file atomically (write temp + rename).
- MUST use template from `sync/status.template.md` or embedded equivalent.
- Field rules per [VESPAWD_BRIDGE_SPEC.md](VESPAWD_BRIDGE_SPEC.md) §6.3.
- MUST set `Last_sync` to ISO-8601 UTC.
- MUST include footer: orchestration projected by Bridge; do not edit manually.

### 7.2 `current_task.md` Notes enrichment

- MUST parse existing Notes section; MUST NOT duplicate keys on re-sync.
- Managed keys (replace if present):
  - `**Vedaws phase:**`
  - `**Orchestration state:**`
  - `**Bridge sync:**`
  - `**Blockers:**`
- MUST NOT modify Goal, Constraints, Acceptance criteria, Status, Progress Log.

### 7.3 Synchronization rules

| Trigger | Projection action |
|---------|-------------------|
| `sync_status` | Full status rewrite |
| `ingest_master_prompt` | Notes + status |
| `post_phase_complete` | status via chained sync |
| `pre_documenter` | status + optional HANDOFF mirror |

### 7.4 Conflict handling

| Conflict | Engine behavior |
|----------|-----------------|
| Vedaws phase ≠ Notes phase | Update Notes to Vedaws; add warning `projection_drift_corrected` |
| Stale HANDOFF | Set Handoff=stale; warning |
| User override skip_design | Design gate field = `skipped` |
| Cannot read current_task | App field = `unknown`; warning |

---

## 8. Validation engine

Composable validators; each returns `{ passed, codes[], messages[] }`.

### 8.1 Doctor validation

| Mode | Rule |
|------|------|
| strict | exit != 0 → `doctor_blocked` |
| soft | exit != 0 → warning only |
| Default strict for `pre_implement_check`, `pre_documenter`; soft for `post_implement` |

### 8.2 Design gate validation

Input: `current_task` text, `design_gate_path`, `skip_design`, `design_later`.

| Condition | Result |
|-----------|--------|
| UI keywords in task + DESIGN not `ready for implementation` + no override | fail `design_gate_blocked` |
| design-only phase | fail if attempting userspace UI without design path update |
| override flags | pass; code `design_gate_overridden` in warnings |

UI keywords list MUST be configurable in manifest `[validation.ui_keywords]`.

### 8.3 Workflow eligibility

Allowed states for implement: `planning`, `ready`, `executing`, `recovering`.

Blocked: `blocked`, `failed`, `awaiting_approval`, `completed`, `archived`, `created` (without bootstrap).

### 8.4 Layout validation

Compare manifest `layout` vs `project_context.md` Mode.

Verify userspace not under `paws022/src/` in sidecar.

### 8.5 Version validation

Compare manifest `vespawd.version`, implementation version, optional `[compat].vedaws`.

---

## 9. Error model

### 9.1 Complete failure and warning codes

| Code | Severity | Description |
|------|----------|-------------|
| `ok` | success | Operation succeeded |
| `vedaws_missing` | blocker | CLI not found |
| `missing_manifest` | blocker | manifest.toml absent |
| `invalid_manifest` | blocker | Schema/required keys fail |
| `invalid_path` | blocker | Resolved path does not exist |
| `layout_conflict` | blocker | Mode mismatch |
| `version_mismatch` | blocker/warn | Semver incompatibility |
| `bootstrap_failed` | blocker | init failed |
| `doctor_blocked` | blocker | doctor hard fail |
| `doctor_warn` | warning | doctor non-zero soft mode |
| `design_gate_blocked` | blocker | UI gate closed |
| `design_gate_overridden` | warning | User skip design |
| `state_ineligible` | blocker | Vedaws state forbids action |
| `state_transition_denied` | blocker | CLI rejected transition |
| `workflow_task_mismatch` | warning | PAWS vs Vedaws task drift |
| `phase_map_miss` | warning | Fallback keyword mapping used |
| `task_complete_denied` | blocker | tasks complete rejected |
| `artifacts_missing` | blocker | software artifacts check fail |
| `orchestration_offline` | warning | Vedaws unavailable; offline projection |
| `sync_incomplete` | warning | Partial sync |
| `workflow_corrupt` | blocker | workflow progress unreadable |
| `cli_failed` | blocker | Non-zero exit |
| `cli_timeout` | blocker | Subprocess timeout |
| `cli_spawn_error` | blocker | Cannot execute |
| `internal_error` | blocker | Unhandled exception |
| `projection_drift_corrected` | warning | Notes updated to match Vedaws |
| `handoff_stale` | warning | HANDOFF footer old |
| `recovery_retry` | info | Retry attempted |

### 9.2 Recovery recommendations

`RecoveryHint` structure:

| Field | Description |
|-------|-------------|
| `code` | Related failure code |
| `action` | Human or Executor action |
| `retry_operation` | Optional operation name to retry |
| `destructive` | boolean; requires `human_approved_destructive_recovery` |

| Code | Recommended action |
|------|-------------------|
| `vedaws_missing` | Install Vedaws; PAWS-only degraded mode |
| `missing_manifest` | Restore `main/bridge/manifest.toml` |
| `bootstrap_failed` | Check logs; run `bootstrap` after fix |
| `doctor_blocked` | Run doctor manually; fix environment |
| `design_gate_blocked` | Complete DESIGN.md or pass skip_design |
| `sync_incomplete` | Retry `sync_status` |
| `workflow_corrupt` | Recovery §10 Bridge Spec; human approval |
| `task_complete_denied` | `workflow show`; fix dependencies |
| `artifacts_missing` | Executor update docs; retry `pre_documenter` |

### 9.3 Retry behavior

- Automatic retry ONLY in CLI adapter for `cli_timeout` and `cli_spawn_error`.
- Operation-level retry: Executor responsibility except idempotent `bootstrap`/`sync_status` safe to call repeatedly.
- MUST NOT auto-retry `post_phase_complete` with same task id more than once per correlation_id.

---

## 10. Logging model

### 10.1 Required log entries

| Event | Fields |
|-------|--------|
| `operation_start` | correlation_id, operation, workspace_root |
| `manifest_loaded` | version, layout |
| `paths_resolved` | pos_root, vedaws_project_root (no secrets) |
| `cli_invoke` | argv, start_ts |
| `cli_complete` | exit_code, duration_ms |
| `validation_fail` | codes |
| `projection_write` | files_touched |
| `operation_end` | ok, codes, duration_ms |

### 10.2 Log levels

| Level | Use |
|-------|-----|
| ERROR | blockers, internal_error |
| WARN | warnings, doctor_warn, drift |
| INFO | operation_start/end, cli_invoke |
| DEBUG | stdout/stderr snippets (truncated) |

### 10.3 Correlation IDs

- MUST propagate from `BridgeContext` or generate UUID per invocation.
- MUST appear in all log lines for that invocation.
- SHOULD be echoed in `BridgeResult.correlation_id`.

### 10.4 Operation timing

- MUST record `duration_ms` on `BridgeResult`.
- SHOULD log per-CLI-call duration at DEBUG.

Log destination: implementation-defined (stderr, file under `main/bridge/logs/`). MUST NOT commit logs with secrets.

---

## 11. Testing strategy

### 11.1 Unit tests

| Module | Focus |
|--------|-------|
| manifest loader | parse, validate, defaults override |
| path resolver | sidecar vs integrated |
| phase map | keyword → task id |
| projection engine | status fields, Notes idempotency |
| validation engine | design gate, eligibility |
| error mapping | exit codes → codes |

MUST use fixtures; MUST NOT require live Vedaws for unit tests.

### 11.2 Integration tests

| Scenario | Requirement |
|----------|-------------|
| Full bootstrap on empty `main/` | `.vedaws/` created via real CLI |
| ingest → sync → pre_implement | against fixture workspace |
| post_phase_complete | task state changes in Vedaws |
| pre_documenter | artifacts command output |

MAY use temporary directories; MUST NOT modify frozen `paws022/` or `vedaws/` trees — copy fixtures.

### 11.3 Recovery tests

| Scenario | Expected |
|----------|----------|
| interrupt after init | re-bootstrap idempotent |
| corrupt workflow-progress | `workflow_corrupt` |
| vedaws missing | offline status projection |
| partial sync fail | `sync_incomplete` + retry succeeds |

### 11.4 Idempotency tests

- Call `bootstrap` 3× sequentially → same end state, `ok=true`.
- Call `sync_status` 5× → stable `status.md` except `Last_sync`.
- Call `ingest_master_prompt` 2× with same input → no duplicate Notes keys.

### 11.5 Executor contract tests

- Golden `BridgeResult` JSON per operation for Executor parser compatibility.
- Verify all §4 sequences emit expected `vedaws_commands_run` audit lists.

---

## 12. Extension points

### 12.1 Future hook system

`hooks/` directory MAY register scripts or modules invoked at:

| Hook | When |
|------|------|
| `after_prepare` | After manifest load |
| `before_cli` | Before each CLI call |
| `after_projection` | After status write |
| `on_failure` | When `ok=false` |

Hooks MUST NOT:

- Modify allowlist CLI commands
- Write `.vedaws/` directly
- Override `ok` without adding codes

Hook interface MUST receive `BridgeContext`, `ResolvedPaths`, read-only `ManifestModel`.

### 12.2 Plugin compatibility

Long-term: Vedaws plugin MAY wrap Bridge public API. v1 Bridge MUST remain **standalone subprocess + file projection**.

Future plugin MUST delegate to same operation handlers for behavioral parity.

### 12.3 Backward compatibility guarantees

| Surface | Guarantee |
|---------|-----------|
| Operation names | Stable; new ops additive only |
| `BridgeResult` fields | Additive; MUST NOT remove fields |
| `manifest.toml` `[vespawd].version` | Minor bump backward compatible |
| `status.md` table columns | Additive columns allowed; MUST NOT remove required columns |
| Phase map keys | Additive |

Breaking changes REQUIRE major `vespawd.version` bump and architecture review.

---

## Appendix A — Operation checklist (implementer)

- [ ] Public API exposes 7 operations
- [ ] Dispatcher prepare pipeline complete
- [ ] CLI allowlist enforced
- [ ] No direct `.vedaws` writes
- [ ] Projection atomic writes
- [ ] Notes enrichment non-destructive
- [ ] All codes in §9.1 implemented
- [ ] Idempotency tests pass
- [ ] Integration tests against real `vedaws` CLI
- [ ] README documents Executor invocation

---

## Appendix B — Synchronization matrix (implementation)

| Artifact | Bridge module | Operation(s) | Write mode |
|----------|---------------|--------------|------------|
| `status.md` | projection | sync_status, * | full replace |
| `current_task.md` Notes | projection | ingest, sync | managed keys only |
| `main/docs/handoff/HANDOFF.md` | projection | pre_documenter | copy mirror OPTIONAL |
| `.vedaws/*` | cli adapter | all mutating | via CLI only |

---

## Appendix C — Example invocation flow (Executor → Bridge)

```
1. Executor writes PAWS scheduler files
2. bridge invoke ingest_master_prompt --context context.json --input ingest.json
3. Bridge returns BridgeResult JSON
4. If ok: bridge invoke pre_implement_check ...
5. If ok: Executor implements userspace
6. bridge invoke post_phase_complete ...
7. bridge invoke sync_status (if not chained)
```

---

## Appendix D — Related documents

| Document | Role |
|----------|------|
| [VESPAWD_BRIDGE_SPEC.md](VESPAWD_BRIDGE_SPEC.md) | Behavioral contract |
| [VESPAWD_EXECUTOR_SPEC.md](VESPAWD_EXECUTOR_SPEC.md) | Invoker sequences |
| [VESPAWD_ARCHITECTURE.md](VESPAWD_ARCHITECTURE.md) | System placement |
| [PLANNER_SPEC.md](PLANNER_SPEC.md) | Phase vocabulary |
| `main/bridge/manifest.toml` | Runtime configuration |

---

*Vespawd Bridge Implementation Specification. Design only — no source code.*
