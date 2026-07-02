# Vespawd Bridge Specification

**Status:** Canonical specification (design only)  
**Audience:** Every Bridge implementation — any invocation mechanism (CLI wrapper, library, Executor subprocess)  
**Prerequisites:** [VESPAWD_ARCHITECTURE.md](VESPAWD_ARCHITECTURE.md), [VESPAWD_EXECUTOR_SPEC.md](VESPAWD_EXECUTOR_SPEC.md), [PLANNER_SPEC.md](PLANNER_SPEC.md)  
**Constraint:** PAWS (`paws022/`) and Vedaws (`vedaws/`) are frozen; the Bridge lives in `main/bridge/` and adapts both without modifying either.

---

## 1. Purpose

### 1.1 What a Bridge is

The **Bridge** is the **synchronization and orchestration adapter** in Vespawd. It is **passive**: invoked by the Executor at defined lifecycle points, never by the Human or Planner directly.

The Bridge:

- Translates Executor-side events (Master Prompt ingest, phase boundaries) into **Vedaws CLI** invocations against `main/`.
- Projects Vedaws orchestration state back into **PAWS human-readable files** (`status.md`, enrichments to `current_task.md`).
- Validates eligibility (doctor, design gate, workflow state) before userspace work proceeds.
- Guarantees **consistency rules** between PAWS memory and Vedaws runtime without merging the two into a single authority.

The Bridge is **not** a runtime, planner, or executor. It is the **adapter** between PAWS conventions and Vedaws mechanics.

### 1.2 Responsibilities

The Bridge **must**:

| Area | Responsibility |
|------|----------------|
| **Bootstrap** | Ensure Vedaws project exists in userspace root; activate software workflow when configured |
| **Ingest** | Map parsed Master Prompt sections to Vedaws phase/task and state transitions |
| **Projection** | Write PAWS scheduler projections from Vedaws snapshots (`status.md`, task id in Notes) |
| **Validation** | Run pre-flight checks: manifest, layout, doctor, design gate, workflow eligibility |
| **CLI invocation** | Call allowed Vedaws commands only; never hand-edit `.vedaws/` files |
| **Completion** | Record task outcomes, trigger `post_phase_complete` automation path |
| **Handoff gate** | Run artifact checklist before documenter phase |
| **Failure reporting** | Return structured pass/fail/blocker results to Executor |
| **Recovery support** | Expose operations idempotent enough to resume after interruption |

### 1.3 What the Bridge must never do

| Forbidden | Reason |
|-----------|--------|
| Plan project scope or emit POS MASTER PROMPTs | Planner role |
| Write or modify `main/src/` userspace code | Executor role |
| Write submission report prose | Documenter role |
| Modify `paws022/.ai/` kernel (except path reads) | Frozen PAWS kernel |
| Modify `vedaws/` runtime source | Frozen Vedaws |
| Directly edit any file under `main/.vedaws/` | Vedaws runtime authority; CLI only |
| Instruct users to hand-edit `.vedaws/` | Public Vespawd rule |
| Override Planner CURRENT TASK goal or acceptance criteria | Scope is Planner + Executor |
| Silently resolve conflicts against spec rules | Must surface blockers |
| Commit/push git | Executor/human only when requested |
| Replace human phase approval | Human gates between phases |
| Invent orchestration state not derivable from inputs | Determinism |

### 1.4 Relationship to other roles

```
Human ──tests, approves──►
Planner ──POS MASTER PROMPT──► Executor ──invoke──► Bridge ──CLI──► Vedaws
                                    │                │
                                    │                └──► project PAWS files (projections)
                                    ├──► PAWS writes (context, task, backlog, HANDOFF)
                                    └──► userspace (main/src/)
Executor ──HANDOFF facts──► Documenter
```

| Role | Interaction with Bridge |
|------|-------------------------|
| **Human** | Indirect. Sees projected `status.md` and Executor blocker messages; never calls Bridge |
| **Planner** | Indirect. Phase vocabulary aligned at ingest; Bridge maps Notes/task id |
| **Executor** | **Sole invoker.** Calls Bridge operations; applies PAWS writes before/after per spec |
| **Vedaws** | Downstream subprocess. Bridge invokes CLI; Vedaws writes `.vedaws/` |
| **Documenter** | Indirect. `pre_documenter` validates artifacts; HANDOFF remains Executor-maintained |

---

## 2. Bridge Lifecycle

### 2.1 Complete lifecycle

```
┌──────────────────────────────────────────────────────────────────┐
│ IDLE          Bridge loaded; manifest valid; awaiting invoke      │
└────────────────────────────┬─────────────────────────────────────┘
                             │ Executor calls operation
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ PREPARE       Load manifest; resolve paths; verify vedaws on PATH │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ EXECUTE       Run operation (bootstrap | ingest | check | …)      │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
                    ┌────────┴────────┐
                    │ Success?        │
                    └────────┬────────┘
              no ◄───────────┼───────────► yes
                │                         │
                ▼                         ▼
┌───────────────────────┐   ┌──────────────────────────────────┐
│ FAIL                  │   │ PROJECT           Update PAWS       │
│ Return error blockers │   │ (if applicable)   projections     │
└───────────────────────┘   └────────────────┬─────────────────┘
                                             ▼
                            ┌──────────────────────────────────┐
                            │ RETURN    Structured result to    │
                            │           Executor                │
                            └────────────────┬─────────────────┘
                                             ▼
                            ┌──────────────────────────────────┐
                            │ IDLE      Await next invocation   │
                            └──────────────────────────────────┘
```

### 2.2 Startup (per invocation)

Each Bridge operation **must**:

1. Load `main/bridge/manifest.toml` (or fail with `missing_manifest`).
2. Resolve POS root, Vedaws project root, userspace path from manifest + `project_context.md`.
3. Verify Vedaws CLI availability (`vedaws version` or equivalent).
4. Validate layout mode (sidecar vs integrated).
5. Proceed to operation body.

### 2.3 Sync (ongoing)

Sync is not a background daemon. **Sync occurs** when Executor invokes `sync_status`, or as final step of `ingest_master_prompt`, `post_phase_complete`, `pre_documenter`.

### 2.4 Validation (gates)

Validation clusters run inside `pre_implement_check`, `pre_documenter`, and partially in `bootstrap` / `ingest_master_prompt`.

### 2.5 Completion

Operation returns **structured result** (§4) to Executor. Bridge does not mark human phase complete — Executor + human approval do.

### 2.6 Recovery

After failure, Bridge operations **must be idempotent** where possible: re-run `bootstrap` on partial init, re-run `sync_status` to reconcile projections.

---

## 3. Initialization

### 3.1 Bootstrap operation overview

**bootstrap** ensures Vedaws orchestration exists for the Vespawd workspace. See §4.1 for full contract.

### 3.2 Project discovery

| Step | Action |
|------|--------|
| 1 | Read `main/bridge/manifest.toml` `[pos]` and `[vedaws]` sections |
| 2 | Read `paws022/.ai/project_context.md` for Mode and Application code path |
| 3 | Confirm Vedaws marker: `main/.vedaws/project.toml` exists **or** bootstrap will create it |
| 4 | Confirm POS marker: `paws022/tasks/` exists |
| 5 | Set **workspace root** = parent of `paws022/` and `main/` in sidecar layout |

### 3.3 Sidecar vs integrated layouts

| Layout | POS root | Vedaws project root | Userspace |
|--------|----------|---------------------|-----------|
| **sidecar** (Vespawd default) | `paws022/` | `main/` | `main/src/` |
| **integrated** | workspace root | workspace root (same) | `src/` at POS root |

Manifest `layout` field must match `project_context.md` Mode. Mismatch → `layout_conflict` failure.

### 3.4 Manifest loading

**Required manifest fields** (conceptual):

| Section | Keys | Purpose |
|---------|------|---------|
| `[vespawd]` | `version` | Bridge spec compatibility |
| `[pos]` | `root`, `current_task`, `handoff`, `design_gate` | PAWS path pointers |
| `[vedaws]` | `project_root`, `workflow_id`, `cli` | Vedaws invocation |
| `[phase_map]` | Planner keyword → Vedaws task id | Ingest mapping |

Missing required keys → `invalid_manifest`. Bridge does not guess paths.

### 3.5 Vedaws initialization

If `main/.vedaws/project.toml` absent:

| Step | Vedaws command |
|------|----------------|
| Init software template | `vedaws init --template software --name <from context> --path <project_root>` |
| Verify | `vedaws doctor --path <project_root>` |

Bridge **never** creates `.vedaws/` by copying static files; **init CLI only**.

### 3.6 Workflow activation

After init or on bootstrap when workflow inactive:

| Step | Vedaws command |
|------|----------------|
| Show workflows | `vedaws workflow show --path <project_root>` |
| Activate software | `vedaws workflow activate software --path <project_root>` |

Default `workflow_id`: `software` per [VESPAWD_ARCHITECTURE.md](VESPAWD_ARCHITECTURE.md).

### 3.7 State transition on bootstrap

After successful init + activate:

| Target state | When |
|--------------|------|
| `initialized` | First-time structure ready |
| `planning` | If ingest immediately follows in same Executor session |

Transitions via `vedaws state transition <state> --path <project_root>` **only** when CLI/eligibility requires; prefer workflow bridge side effects from ingest.

### 3.8 Bootstrap failure behavior

| Failure | Bridge result | Executor guidance |
|---------|---------------|-------------------|
| Vedaws not installed | `vedaws_missing` | PAWS-only degraded mode warning |
| init fails | `bootstrap_failed` | Block orchestration; PAWS writes may continue |
| doctor hard fail | `doctor_blocked` | `Status: blocked` |
| manifest invalid | `invalid_manifest` | Fix manifest before retry |
| layout conflict | `layout_conflict` | Fix project_context vs manifest |

---

## 4. Bridge Operations

All operations are **synchronous** from Executor's perspective. Each returns a **BridgeResult** (conceptual):

| Field | Type | Meaning |
|-------|------|---------|
| `ok` | boolean | Operation succeeded |
| `operation` | string | Operation name |
| `blockers` | list | Human-readable blocker messages |
| `warnings` | list | Non-fatal issues |
| `vedaws_task_id` | string | Active software.* task if known |
| `project_state` | string | Vedaws lifecycle state name |
| `doctor_summary` | string | Truncated doctor output |
| `files_touched` | list | PAWS projection paths written |

---

### 4.1 `bootstrap`

| Aspect | Specification |
|--------|---------------|
| **Purpose** | First-time or recovery setup of Vedaws project and workflow in userspace root |
| **Inputs** | `workspace_root`; optional `project_name` from context |
| **Outputs** | BridgeResult; `.vedaws/` created via CLI if absent |
| **PAWS files affected** | `paws022/tasks/status.md` (via follow-up sync); may set Notes in `current_task.md` if present |
| **Vedaws commands** | `vedaws init --template software`; `vedaws workflow activate software`; `vedaws doctor`; `vedaws state transition initialized` (if needed) |
| **Failure handling** | See §3.8; idempotent re-run if `.vedaws/` partially exists |

**Invocation:** Executor startup or first Master Prompt before ingest.

---

### 4.2 `ingest_master_prompt`

| Aspect | Specification |
|--------|---------------|
| **Purpose** | Align Vedaws orchestration with newly parsed POS MASTER PROMPT after Executor writes PAWS scheduler files |
| **Inputs** | Structured parse: `project_context_updates`, `current_task` (goal, criteria, notes), `backlog_items`, optional `phase_hint` from Notes |
| **Outputs** | BridgeResult with `vedaws_task_id`, eligibility, blockers |
| **PAWS files affected** | Enriches `current_task.md` **Notes** with `Vedaws phase: software.<id>`; triggers `sync_status` → `status.md` |
| **Vedaws commands** | `vedaws workflow show`; state transition toward `planning`/`executing` if eligible; optional `vedaws run --path` (dispatch only if design allows non-userspace workers — default **no** on ingest) |
| **Failure handling** | If phase unmapped, `phase_map_miss` warning + best-effort keyword match; if transition rejected, `state_transition_denied` blocker |

**Precondition:** Executor has already written `current_task.md`, `backlog.md`, merged `project_context.md`.

**Phase mapping** (default `[phase_map]`):

| Signal in CURRENT TASK / Notes | Vedaws task id |
|-------------------------------|----------------|
| scope, requirements, MVP | `scope` |
| architecture, components, ADR | `architecture` |
| api, schema, contracts | `api-design` |
| implement, feature, build | `implement` |
| test, verify, demo | `test` |
| review, lint, fix pass | `review` |
| handoff, submission package | `handoff` |

**Sync project name:** merge product name from context into Vedaws via init metadata or config only through CLI-supported surfaces — never raw TOML edit.

---

### 4.3 `sync_status`

| Aspect | Specification |
|--------|---------------|
| **Purpose** | Project Vedaws orchestration snapshot into PAWS `status.md` and optional `current_task.md` Notes |
| **Inputs** | Resolved paths from manifest |
| **Outputs** | BridgeResult; written projection files list |
| **PAWS files affected** | `paws022/tasks/status.md` (primary); optional Notes append in `current_task.md` |
| **Vedaws commands** | `vedaws status --path <project_root>`; `vedaws workflow show --path <project_root>` |
| **Failure handling** | If Vedaws unavailable, write `status.md` with `orchestration: offline`; do not delete prior snapshot |

**status.md projection fields** (minimum):

| Field | Source |
|-------|--------|
| Phase | Vedaws active workflow task or project state |
| App | Derived from `current_task.md` Status |
| Handoff | `fresh` if HANDOFF footer updated within policy; else `stale` |
| Docs (submission) | Rubric/doc phase pending/complete |
| Orchestration | Vedaws project state name |
| Last_sync | Timestamp |
| Blockers | From doctor/eligibility if any |

---

### 4.4 `pre_implement_check`

| Aspect | Specification |
|--------|---------------|
| **Purpose** | Gate before Executor edits userspace (`main/src/`) |
| **Inputs** | `current_task` content; design gate path; user override flags (`skip design`, `design later`) from Executor session |
| **Outputs** | BridgeResult `ok: true` or blockers list |
| **PAWS files affected** | None required; may set `current_task.md` `Status: blocked` **via Executor** on failure |
| **Vedaws commands** | `vedaws doctor --path <project_root>`; `vedaws workflow show`; eligibility read from status |
| **Failure handling** | Return `design_gate_blocked`, `doctor_blocked`, `state_ineligible`, `workflow_task_mismatch` |

**Checks (all applicable):**

1. Manifest + layout valid  
2. Doctor: no unacknowledged hard failures  
3. Design gate (§8.2)  
4. Vedaws state allows dispatch (`planning`, `ready`, `executing`, `recovering` per eligibility)  
5. Mapped workflow task matches CURRENT TASK phase (warning if soft mismatch)

---

### 4.5 `post_implement`

| Aspect | Specification |
|--------|---------------|
| **Purpose** | Post-userspace-edit orchestration hooks (automation, git worker) without closing phase |
| **Inputs** | List of changed paths (from Executor); active `vedaws_task_id` |
| **Outputs** | BridgeResult with automation/worker summaries |
| **PAWS files affected** | None directly |
| **Vedaws commands** | `vedaws run --path <project_root>` (bounded iteration); captures worker events |
| **Failure handling** | Warnings only unless worker hard-fails task; does not mark phase complete |

**Invocation:** Optional after significant `main/src/` edits during long implement phases; required before `post_phase_complete` if automation must run mid-phase.

---

### 4.6 `post_phase_complete`

| Aspect | Specification |
|--------|---------------|
| **Purpose** | Record completion of active Vedaws workflow task when Executor acceptance criteria met |
| **Inputs** | `vedaws_task_id`; `outcome` (`completed` \| `failed` \| `blocked`); optional `reason` |
| **Outputs** | BridgeResult; updated orchestration snapshot |
| **PAWS files affected** | Via `sync_status` → `status.md` |
| **Vedaws commands** | `vedaws tasks complete software.<id> --path <project_root>` (or equivalent); `vedaws run --path` for automation; state transition toward `awaiting_approval` if human gate |
| **Failure handling** | If complete rejected (dependencies), return `task_complete_denied` with workflow show excerpt |

**Invocation:** Executor §10 after acceptance verified.

---

### 4.7 `pre_documenter`

| Aspect | Specification |
|--------|---------------|
| **Purpose** | Validate artifact completeness before Human sends HANDOFF to Documenter |
| **Inputs** | Resolved paths |
| **Outputs** | BridgeResult with artifact checklist |
| **PAWS files affected** | May mirror HANDOFF facts to `main/docs/handoff/HANDOFF.md` **copy only** if Executor already wrote PAWS HANDOFF |
| **Vedaws commands** | `vedaws software artifacts --path <project_root>`; `vedaws doctor`; `vedaws tasks complete software.handoff` when criteria met |
| **Failure handling** | `artifacts_missing` blocker with missing paths list |

**Invocation:** Handoff phase or Executor-declared feature-complete.

---

## 5. Synchronization Model

### 5.1 Authoritative sources

| Domain | Authoritative | Consumers |
|--------|---------------|-----------|
| Orchestration eligibility | `main/.vedaws/state.toml` + workflow engine | Bridge, Vedaws |
| Workflow task progress | `main/.vedaws/workflow-progress.json` | Bridge, Vedaws |
| Product facts | `paws022/.ai/project_context.md` | Executor, Planner, Bridge (read) |
| Active task criteria | `paws022/tasks/current_task.md` (from Planner via Executor) | Human, Executor, Bridge (read) |
| Future work queue | `paws022/tasks/backlog.md` | Planner, Executor |
| Phase snapshot (human) | `paws022/tasks/status.md` | Human (**projection**) |
| Submission facts | `paws022/docs/HANDOFF_FOR_DOCUMENTER.md` | Documenter, Executor |
| Application code | `main/src/` | Executor only |

### 5.2 PAWS projections

Files the Bridge **may write or enrich** (never replace Planner content in backlog/task goal):

| File | Bridge write mode |
|------|-------------------|
| `status.md` | **Full projection** from Vedaws + freshness checks |
| `current_task.md` | **Notes append only** (Vedaws task id, blockers, sync timestamp) — never overwrite Goal/Criteria |
| `backlog.md` | **No write** — Executor/Planner only |
| `HANDOFF_FOR_DOCUMENTER.md` | **No write** — Executor only; Bridge may read for freshness |
| `project_context.md` | **No write** — Executor only; Bridge reads for layout/name |

### 5.3 Vedaws runtime

All Vedaws mutations go through **CLI subprocess** with `--path <vedaws_project_root>`. Bridge never:

- Opens `.vedaws/*.toml` for write  
- Patches `workflow-progress.json`  
- Edits `transitions.jsonl`

### 5.4 Conflict resolution

| Conflict | Resolution |
|----------|------------|
| `current_task.md` phase vs Vedaws active task | **Vedaws wins** for eligibility; Bridge appends explanation to Notes; Executor may request Planner correction |
| `project_context.md` name vs `project.toml` name | **PAWS wins** for display; Bridge triggers CLI sync only if Vedaws supports it; else warning |
| `status.md` stale but Vedaws progressed | **Re-project** on next `sync_status` |
| HANDOFF stale, Vedaws handoff task complete | **Warning** to Executor; refresh HANDOFF before documenter |
| design gate vs user **skip design** | **User override wins** for this session; record override in Notes |
| Kernel vs memory (PAWS) | **Memory wins** per PAWS rules; Bridge does not edit kernel |

### 5.5 Synchronization matrix

See Appendix B.

### 5.6 Synchronization order

**Master Prompt ingest** (Executor-coordinated):

```
1. Executor → project_context.md, current_task.md, backlog.md
2. Bridge → ingest_master_prompt
3. Bridge → sync_status → status.md
4. Executor → HANDOFF seed
```

**After implementation:**

```
1. Executor → userspace + docs
2. Bridge → post_implement (optional)
3. Bridge → post_phase_complete
4. Bridge → sync_status
5. Executor → HANDOFF refresh, completed/
```

**Handoff:**

```
1. Bridge → pre_documenter
2. Executor → HANDOFF final refresh
3. Bridge → sync_status
```

---

## 6. State Projection

### 6.1 Vedaws → PAWS projection map

```
main/.vedaws/state.toml              ──► status.md :: Orchestration
main/.vedaws/workflow-progress.json  ──► status.md :: Phase
                                       ──► current_task.md :: Notes (vedaws_task_id)
vedaws workflow show (CLI)             ──► status.md :: Phase detail
vedaws doctor (CLI)                    ──► status.md :: Blockers
HANDOFF footer timestamp              ──► status.md :: Handoff fresh/stale
paws022/design/DESIGN.md status       ──► status.md :: Design gate
paws022/tasks/current_task.md Status  ──► status.md :: App
```

### 6.2 `current_task.md` enrichment

Bridge **must not** replace Goal, Constraints, or Acceptance criteria.

Allowed **Notes** appendages:

```markdown
### Notes
...
- **Vedaws phase:** software.implement
- **Orchestration state:** executing
- **Bridge sync:** 2026-07-01T12:00:00Z
- **Blockers:** <from doctor or design gate>
```

### 6.3 `status.md` template (projected)

```markdown
# POS status

| Field | Value |
|-------|--------|
| Phase | <workflow task or planning phase> |
| App | <idle \| in_progress \| blocked from current_task> |
| Handoff | <fresh \| stale> |
| Docs (submission) | <pending \| ready> |
| Orchestration | <vedaws state name> |
| Design gate | <open \| ready \| skipped> |
| Last_sync | <ISO timestamp> |
| Blockers | <none or list> |

_Orchestration projected by Vespawd Bridge. Do not edit manually._
```

### 6.4 `backlog.md`

Bridge **reads** for phase ordering validation only. **No projection write.**

### 6.5 `HANDOFF_FOR_DOCUMENTER.md`

Bridge **reads** footer timestamp for `Handoff` field. Optional **one-way mirror** to `main/docs/handoff/HANDOFF.md` for `vedaws software artifacts` — copy Executor content only, never author prose.

### 6.6 `project_context.md`

Bridge **reads** Mode, Application code, product name. No routine projection write.

---

## 7. Vedaws Integration

### 7.1 Allowed CLI commands

Bridge **may** invoke only:

| Command | Use |
|---------|-----|
| `vedaws version` | CLI presence check |
| `vedaws init --template software [--name] [--path]` | Bootstrap |
| `vedaws doctor --path` | Health gate |
| `vedaws status --path` | Snapshot |
| `vedaws workflow show --path` | Task progress |
| `vedaws workflow activate <id> --path` | Bootstrap |
| `vedaws run --path` | Dispatch/automation loop |
| `vedaws tasks complete <workflow.task> --path` | Phase complete |
| `vedaws tasks show --path` | Diagnostics |
| `vedaws state --path` | State read |
| `vedaws state transition <state> --path` | When ingest/complete requires |
| `vedaws state history --path` | Recovery diagnostics |
| `vedaws software artifacts --path` | Handoff gate |

Commands **not** in this list require architecture review before Bridge use.

### 7.2 Workflow activation

- Default workflow: `software`
- Activate once per project unless deactivated by corruption recovery
- Idempotent: re-activate no-op if already active

### 7.3 Doctor

- Run on `bootstrap`, `pre_implement_check`, `pre_documenter`
- Parse exit code and summary text
- **Hard fail** → block userspace work
- **Soft warn** → include in BridgeResult.warnings

### 7.4 Workflow show

- Extract active task id, READY/COMPLETED states, blocked dependencies
- Map to `status.md` Phase field

### 7.5 Task completion

- Format: `software.<task_id>` (e.g. `software.implement`)
- Complete only when Executor signals `post_phase_complete`
- Never complete tasks not mapped from current phase without Executor override flag

### 7.6 State transitions

Bridge requests transitions **only** through CLI:

| Trigger | Typical target state |
|---------|---------------------|
| bootstrap complete | `initialized` |
| ingest_master_prompt | `planning` or `executing` |
| post_phase_complete (human gate) | `awaiting_approval` |
| pre_documenter success | `completed` (optional) |
| doctor hard failure | `blocked` |

Bridge does not invent transitions outside `vedaws/design/006_STATE_MACHINE.md` valid edges.

### 7.7 `.vedaws` edit prohibition

| Action | Allowed |
|--------|---------|
| CLI mutates `.vedaws/` | Yes |
| Bridge opens `.vedaws/` read-only | Yes (diagnostics only if CLI insufficient) |
| Bridge writes `.vedaws/` directly | **Never** |
| Executor writes `.vedaws/` | **Never** |
| Human manual edit | **Discouraged**; recovery only |

---

## 8. Validation

### 8.1 Doctor validation

| Level | Behavior |
|-------|----------|
| Hard fail | Block `pre_implement_check`; `doctor_blocked` |
| Soft warn | Proceed; list in warnings |
| Unavailable | `vedaws_missing`; degraded mode |

### 8.2 Design gate validation

| Check | Rule |
|-------|------|
| UI named in CURRENT TASK? | If yes, read `design_gate` path from manifest |
| DESIGN.md status | Must be `ready for implementation` unless Executor passed user override |
| Screens listed | Task screens must appear in DESIGN.md table or Notes cite override |
| Design-only phase | If goal is design-only, gate inverted: must **not** require ready for code |

Source: `paws022/docs/UI_DESIGN.md`, Executor spec §6.

### 8.3 Workflow eligibility validation

| Vedaws state | Userspace implement allowed |
|--------------|----------------------------|
| `planning`, `ready`, `executing`, `recovering` | Yes (if other checks pass) |
| `blocked`, `failed` | No |
| `awaiting_approval` | No (human gate) |
| `completed`, `archived` | No |

### 8.4 Layout validation

| Check | Failure code |
|-------|--------------|
| POS root exists | `pos_missing` |
| Userspace parent exists | `userspace_missing` |
| Sidecar: no `paws022/src/` as app | `wrong_userspace` |
| manifest.layout matches context Mode | `layout_conflict` |

### 8.5 Manifest validation

| Check | Failure code |
|-------|--------------|
| File exists | `missing_manifest` |
| Required sections present | `invalid_manifest` |
| Paths resolve relative to workspace | `invalid_path` |
| `vespawd.version` compatible | `version_mismatch` |

### 8.6 Project integrity validation

| Check | When |
|-------|------|
| `.vedaws/project.toml` present post-bootstrap | bootstrap, ingest |
| Software workflow definition exists | bootstrap |
| `plugins.toml` includes software plugin | bootstrap |
| Phase map non-empty | ingest |

---

## 9. Failure Handling

### 9.1 Missing Vedaws

| Symptom | Bridge behavior |
|---------|-----------------|
| `vedaws` not on PATH | `ok: false`, `vedaws_missing`; PAWS projections optional offline stamp |
| Executor | Continue PAWS-only with explicit warning; block orchestration-dependent gates |

### 9.2 Missing manifest

| Symptom | Bridge behavior |
|---------|-----------------|
| No `main/bridge/manifest.toml` | All operations fail `missing_manifest` |
| Executor | Use hardcoded Vespawd sidecar defaults **only** if spec-approved fallback document exists; else block |

### 9.3 Doctor failures

| Symptom | Bridge behavior |
|---------|-----------------|
| Hard fail | `pre_implement_check` fails; blockers in result |
| Executor | `Status: blocked`; surface doctor summary |

### 9.4 Workflow corruption

| Symptom | Bridge behavior |
|---------|-----------------|
| Invalid `workflow-progress.json` | `workflow_corrupt`; suggest recovery §10.3 |
| Missing workflow file | Re-run `bootstrap` activate step |

### 9.5 Partial sync

| Symptom | Bridge behavior |
|---------|-----------------|
| ingest succeeded; sync_status failed | Return partial result; Notes flag `sync_incomplete` |
| Executor | Retry `sync_status` before implement |

### 9.6 Stale PAWS files

| Symptom | Bridge behavior |
|---------|-----------------|
| `status.md` older than Vedaws transition | Overwrite on `sync_status` |
| HANDOFF older than complete handoff task | Warning in `pre_documenter` |

### 9.7 Stale Vedaws state

| Symptom | Bridge behavior |
|---------|-----------------|
| Vedaws shows completed task; PAWS still in_progress | Notes mismatch warning; prefer Vedaws for eligibility |
| Human approved next phase but Vedaws not ingested | Re-run `ingest_master_prompt` |

---

## 10. Recovery Workflow

### 10.1 Interrupted sync

```
1. Executor retries bridge.sync_status
2. If still failing, bridge.ingest_master_prompt with last parsed sections (idempotent)
3. Compare workflow show vs current_task Notes
4. Report residual drift to human
```

### 10.2 Bootstrap failure

```
1. Capture CLI stderr in BridgeResult
2. If .vedaws/ partial, vedaws doctor --path
3. If doctor repairable, retry bootstrap
4. Else PAWS-only mode until human fixes environment
```

### 10.3 Corrupted workflow

```
1. vedaws workflow show --path (diagnose)
2. vedaws state history --path
3. If unrecoverable: human backs up main/.vedaws/
4. Re-run vedaws init --template software (destructive — requires human approval)
5. bootstrap + re-ingest from last Master Prompt
```

### 10.4 Project relocation

```
1. Human moves workspace root
2. Update manifest paths if absolute paths used
3. Update project_context.md paths
4. Re-run bootstrap + sync_status
5. Verify vedaws doctor --path from new location
```

### 10.5 Sidecar migration

```
1. Human converts integrated → sidecar or reverse (architecture change)
2. Update project_context Mode + manifest layout
3. Move userspace to match (main/src vs src)
4. bootstrap validates layout
5. Planner may need realignment Master Prompt
```

---

## 11. Compatibility

### 11.1 Architecture Spec

| Requirement | Bridge compliance |
|-------------|-------------------|
| Bridge in `main/bridge/` | Yes |
| Sidecar layout default | Yes |
| Software workflow phases | Phase map §4.2 |
| Executor invokes Bridge | Sole entry point |
| No `.vedaws` hand edit | §7.7 |

### 11.2 Planner Spec

| Requirement | Bridge compliance |
|-------------|-------------------|
| Phase ids in Notes | ingest maps to software.* |
| BACKLOG not written by Bridge | §5.2 |
| Documenter last | pre_documenter validates only |

### 11.3 Executor Spec

| Requirement | Bridge compliance |
|-------------|-------------------|
| Operation names match | §4 |
| Sync order §5.3 / Executor §5.3 | Identical |
| pre_implement before userspace | §4.4 |
| post_phase_complete after acceptance | §4.6 |
| Vedaws CLI only | §7 |

### 11.4 PAWS

| Requirement | Bridge compliance |
|-------------|-------------------|
| PAWS memory paths | Via manifest pointers |
| Kernel read-only | §1.3 |
| status/current_task conventions | §6 |
| Design gate | §8.2 |

### 11.5 Vedaws

| Requirement | Bridge compliance |
|-------------|-------------------|
| state.toml authoritative | §5.1 |
| CLI public API only | §7.1 |
| software workflow | Default workflow_id |
| No runtime source changes | §1.3 |

### 11.6 Versioning

Manifest `vespawd.version` must declare compatible triple:

- Bridge spec version  
- Minimum Vedaws architecture version (0.5.0)  
- POS instructionsVersion range (informational)

Mismatch → `version_mismatch` warning or hard fail per policy.

---

## 12. Design Goals

| Goal | Bridge mechanism |
|------|------------------|
| **Deterministic synchronization** | Fixed operation set, ordered sync §5.6, explicit authority §5.1 |
| **Minimal hallucination** | No scope decisions; no HANDOFF prose; phase map table-driven |
| **Resumability** | Idempotent bootstrap/ingest/sync; recovery §10 |
| **Predictable orchestration** | Vedaws wins eligibility; doctor gates |
| **Compatibility** | PAWS + Vedaws frozen; adapter-only §11 |
| **Maintainability** | Manifest-driven paths; single CLI integration surface |
| **Passive adapter** | Executor-only invoke §1.1 |
| **Human legibility** | Project to status.md §6.3 |
| **Tool neutrality** | No IDE references §12.1 |

### 12.1 Tool neutrality

- Bridge is invoked by Executor through **implementation-defined** mechanism (subprocess CLI to bridge binary, shell script, or library call).
- No IDE, vendor, or model names in normative behavior.
- Optional: `main/bridge/hooks/` as documented extension points — hooks must not change §4 contracts.

---

## Appendix A — Operation checklist

Executor session checklist (Bridge operations marked **B**):

- [ ] **B** `bootstrap` (first run / missing `.vedaws/`)
- [ ] Executor writes PAWS files from Master Prompt
- [ ] **B** `ingest_master_prompt`
- [ ] **B** `sync_status`
- [ ] **B** `pre_implement_check`
- [ ] Executor implements userspace
- [ ] **B** `post_implement` (optional)
- [ ] **B** `post_phase_complete`
- [ ] **B** `sync_status`
- [ ] **B** `pre_documenter` (handoff phase)
- [ ] Executor final HANDOFF refresh

---

## Appendix B — Synchronization matrix

| Artifact | Writer (primary) | Bridge role | Vedaws authority | On conflict |
|----------|------------------|-------------|----------------|-------------|
| `project_context.md` | Executor | Read | — | PAWS memory wins |
| `current_task.md` Goal/Criteria | Executor | Notes enrich | — | Planner/Executor |
| `current_task.md` Status | Executor | Read | — | Executor |
| `backlog.md` | Executor | Read | — | Planner |
| `status.md` | Bridge | Project | Vedaws snapshot | Re-project |
| `HANDOFF_FOR_DOCUMENTER.md` | Executor | Read/mirror | — | Executor |
| `main/docs/handoff/HANDOFF.md` | Executor (mirror) | Optional copy | Artifact check | PAWS HANDOFF |
| `main/.vedaws/state.toml` | Vedaws CLI | Indirect | **Yes** | Vedaws wins |
| `workflow-progress.json` | Vedaws CLI | Indirect | **Yes** | Vedaws wins |
| `main/src/` | Executor | None | — | Executor |

---

## Appendix C — Example lifecycle

**Phase: first implement** (sidecar layout)

```
1. Human pastes Master Prompt → Executor
2. Executor parses; writes context, current_task, backlog
3. Bridge.bootstrap
   → vedaws init --template software --path main
   → vedaws workflow activate software --path main
   → vedaws doctor --path main
4. Bridge.ingest_master_prompt
   → maps to software.implement
   → state transition executing (if eligible)
5. Bridge.sync_status → status.md Phase=implement, Orchestration=executing
6. Bridge.pre_implement_check
   → doctor pass
   → design gate: DESIGN.md ready OR non-UI task
7. Executor implements main/src/
8. Bridge.post_implement (optional) → vedaws run --path main
9. Bridge.post_phase_complete → vedaws tasks complete software.implement
10. Bridge.sync_status → Phase awaiting next; App in_progress until Executor idles
11. Executor updates HANDOFF; human tests
12. Human → Planner follow-up for test phase
```

---

## Appendix D — Related documents

| Document | Role |
|----------|------|
| [VESPAWD_ARCHITECTURE.md](VESPAWD_ARCHITECTURE.md) | Bridge layer design §9 |
| [VESPAWD_EXECUTOR_SPEC.md](VESPAWD_EXECUTOR_SPEC.md) | Invoker contract |
| [PLANNER_SPEC.md](PLANNER_SPEC.md) | Phase vocabulary |
| [START_HERE.md](START_HERE.md) | Human-visible workflow |
| `vedaws/design/007_PROJECT_MODEL.md` | `.vedaws/` layout |
| `vedaws/design/006_STATE_MACHINE.md` | State transitions |
| `paws022/docs/UI_DESIGN.md` | Design gate |
| `vedaws/plugins/software/templates/project/workflows/software.workflow.toml` | Workflow tasks |

---

*Canonical Vespawd Bridge Specification. Design only — no implementation.*
