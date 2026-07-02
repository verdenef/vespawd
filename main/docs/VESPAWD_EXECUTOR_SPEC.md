# Vespawd Executor Specification

**Status:** Canonical specification (design only)  
**Audience:** Every Executor implementation — any IDE, any coding agent  
**Prerequisites:** [VESPAWD_ARCHITECTURE.md](VESPAWD_ARCHITECTURE.md), `paws022/.ai/executor_rules.md`  
**Constraint:** PAWS (`paws022/`) and Vedaws (`vedaws/`) are frozen; this spec defines Vespawd behavior in `main/` and PAWS memory paths.

---

## 1. Purpose

### 1.1 What an Executor is

The **Executor** is the **implementation agent** in Vespawd. It runs inside the user's IDE (or equivalent coding environment) and is the only role that **writes application code**, **updates project memory**, and **maintains the submission handoff**.

The user pastes a **POS MASTER PROMPT** (produced by an external Planner) into the Executor's chat. The Executor parses it, synchronizes project state, invokes the Bridge and Vedaws as required, implements work in userspace, and records outcomes in PAWS markdown files.

### 1.2 Responsibilities

The Executor **must**:

| Area | Responsibility |
|------|----------------|
| **Intake** | Parse POS MASTER PROMPT sections deterministically |
| **Memory** | Merge context, write `current_task.md`, append backlog, update docs when boundaries change |
| **Scheduler** | Reflect active phase; mark completion; log to `tasks/completed/` |
| **Userspace** | Implement acceptance criteria in the application code path (`main/src/` in sidecar layout) |
| **Design gate** | Enforce `design/DESIGN.md` before new major UI |
| **Handoff** | Maintain `HANDOFF_FOR_DOCUMENTER.md` with facts only |
| **Bridge** | Trigger bridge operations at defined lifecycle points |
| **Vedaws** | Invoke CLI subprocesses against `main/`; never ask users to edit `.vedaws/` |
| **Reporting** | Summarize how to run and test; state blockers clearly |

### 1.3 What the Executor must never do

| Forbidden | Reason |
|-----------|--------|
| Produce POS MASTER PROMPTs | Planner role only (`paws022/.ai/planner_prompt.md`) |
| Write submission report prose | Documenter role; HANDOFF is facts only |
| Modify `paws022/.ai/` kernel files (except `project_context.md`) | Template/org updates only |
| Modify `vedaws/` frozen runtime source | Vespawd integrates, does not fork Vedaws |
| Edit `main/.vedaws/*` by hand or instruct users to do so | Orchestration authority is runtime-managed |
| Invent features not in Master Prompt, HANDOFF, or project memory | Minimizes hallucination |
| Invent API keys, secrets, or credentials | Security; use env placeholders |
| Commit or push to git unless user explicitly requests | `paws022/.ai/coding_rules.md` |
| Redesign architecture beyond task scope | Minimal diff philosophy |
| Bypass design gate for listed screens without user **skip design** / **design later** | `paws022/docs/UI_DESIGN.md` |
| Replace human phase approval | User tests between Planner phases |

### 1.4 Relationship to other roles

```
Human ──provides assignment, tests, approves phases──►
Planner ──POS MASTER PROMPT──► Executor ──facts──► Documenter
                                  │
                                  ├──► PAWS memory (paws022/)
                                  ├──► Userspace (main/src/)
                                  ├──► Bridge (main/bridge/)
                                  └──► Vedaws CLI ──► main/.vedaws/
```

| Role | Interaction with Executor |
|------|---------------------------|
| **Planner** | Upstream. Supplies structured intent. Executor never replans multi-phase scope. |
| **Bridge** | Sidecar sync layer. Executor calls defined operations; Bridge translates PAWS ↔ Vedaws. |
| **Vedaws** | Background orchestration. Executor invokes CLI; does not embed runtime internals. |
| **Documenter** | Downstream. Consumes HANDOFF + rubric after build. Executor does not write report sections. |
| **Human** | Gates progress. Executor implements; human verifies before next Planner phase. |

---

## 2. Executor Lifecycle

Complete lifecycle from receiving a POS MASTER PROMPT until the phase is closed.

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. RECEIVE    User pastes POS MASTER PROMPT (or legacy alias)    │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. STARTUP    Read order, validate, discover layout, bridge boot  │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. PARSE      Extract all Master Prompt sections                  │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. SYNC       Write PAWS files; bridge.ingest_master_prompt        │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ 5. GATE       Design gate + bridge.pre_implement_check             │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
                    ┌────────┴────────┐
                    │ Blocked?        │
                    └────────┬────────┘
              yes ◄──────────┼──────────► no
                │                         │
                ▼                         ▼
┌───────────────────────┐   ┌──────────────────────────────────┐
│ 6a. FAIL              │   │ 6b. IMPLEMENT  Userspace + docs   │
│ Update task blocked   │   └────────────────┬─────────────────┘
│ Report to human       │                    ▼
└───────────────────────┘   ┌──────────────────────────────────┐
                            │ 7. VERIFY  Self-check acceptance   │
                            └────────────────┬─────────────────┘
                                             ▼
                            ┌──────────────────────────────────┐
                            │ 8. COMPLETE  HANDOFF, completed/ │
                            │ bridge.post_phase_complete       │
                            └────────────────┬─────────────────┘
                                             ▼
                            ┌──────────────────────────────────┐
                            │ 9. REPORT  Run/test summary       │
                            │ Human tests → Planner or fix loop  │
                            └──────────────────────────────────┘
```

**One Master Prompt = one active phase.** The Executor does not advance to backlog items without a new Master Prompt from the Planner (except documenting them in `backlog.md`).

---

## 3. Startup Sequence

The Executor **must** complete startup **before writing any userspace code**.

### 3.1 Trigger recognition

Startup begins when the user:

- Pastes a document whose first heading is `# POS MASTER PROMPT`, or
- Pastes a legacy `# CURSOR MASTER PROMPT`, or
- Explicitly says **execute master prompt** (or equivalent) with a Master Prompt body.

Short natural-language tasks **without** a Master Prompt: Executor still writes `current_task.md` before coding (`paws022/.ai/executor_rules.md`).

### 3.2 Required files to read

Paths are relative to **POS root** (`paws022/` in Vespawd sidecar layout) unless noted.

| Priority | File | Purpose |
|----------|------|---------|
| 1 | `paws022/.ai/project_context.md` | Product, stack, layout mode, userspace path |
| 2 | `paws022/tasks/current_task.md` | Prior active task (if any) |
| 3 | `paws022/tasks/status.md` | Phase snapshot |
| 4 | `main/bridge/manifest.toml` | Vespawd layout pointers (when present) |
| 5 | Relevant `paws022/docs/` | Before boundary changes (see §3.3) |
| 6 | `paws022/design/DESIGN.md`, `design/sources.md` | Before new/changed UI |
| 7 | `paws022/.ai/system_prompt.md` | Layer model |
| 8 | `paws022/.ai/architecture_rules.md`, `coding_rules.md`, `workflow.md`, `debugging_protocol.md` | As needed |

After parsing the incoming Master Prompt, re-read **CURRENT TASK** acceptance criteria from the parsed content (authoritative for this run).

### 3.3 Read order rule

**Memory before kernel rules before implementation.** If `project_context.md` and kernel rules conflict, **memory wins**; record exceptions in `paws022/docs/decisions.md`.

### 3.4 Validation

Before parse/write/sync, validate:

| Check | On failure |
|-------|------------|
| Master Prompt contains required H2 sections (§4) | Request complete prompt from user; do not implement |
| Workspace layout discoverable (`project_context.md` or `bridge/manifest.toml`) | Run bridge bootstrap or ask user to confirm paths |
| Userspace path resolvable | Sidecar: `main/src/`; integrated: `src/` per context |
| No concurrent `current_task.md` with `Status: in_progress` for a **different** goal unless user confirms supersede | Ask once; then overwrite per new Master Prompt |

### 3.5 Project discovery

Resolve paths:

| Concept | Vespawd sidecar default | Source |
|---------|-------------------------|--------|
| POS root | `paws022/` | `project_context.md` Mode: sidecar |
| Userspace | `main/src/` | `project_context.md` Application code |
| Vedaws project root | `main/` | `main/.vedaws/project.toml` |
| Design artifacts | `paws022/design/` | PAWS contract |

Executor opens **workspace root** (parent of `paws022/` and `main/`), not `paws022/` alone.

### 3.6 Bridge initialization

On first execution or if `main/.vedaws/` is missing:

1. Invoke **bridge.bootstrap** (or equivalent): `vedaws init --template software` in `main/` if not initialized.
2. Ensure software workflow is activatable.
3. Load `main/bridge/manifest.toml` for phase map and path pointers.

If bridge is not yet implemented, Executor performs documented manual equivalents: init Vedaws project, then continue PAWS file writes; record orchestration gap in `current_task.md` Notes.

### 3.7 Orchestration synchronization

After bridge bootstrap:

1. Invoke **bridge.sync_status** (or `vedaws status --path main`) to refresh baseline.
2. If `vedaws doctor --path main` reports **blocking** issues, set `current_task.md` `Status: blocked` and report; do not implement until resolved or user overrides.

Only after startup completes may the Executor modify userspace code.

---

## 4. Master Prompt Parsing

### 4.1 Document structure

Required sections **in order** (`paws022/.ai/planner_prompt.md`):

1. H1: `# POS MASTER PROMPT`
2. H2: `PROJECT BRIEF`
3. H2: `PROJECT CONTEXT UPDATES`
4. H2: `CURRENT TASK`
5. H2: `BACKLOG ITEMS`
6. H2: `EXECUTOR INSTRUCTIONS` (legacy alias: `CURSOR INSTRUCTIONS`)

No content before the H1 line. Planner output is the single source of truth for this run.

### 4.2 Section: PROJECT BRIEF

| Aspect | Specification |
|--------|---------------|
| **Content** | Assignment summary, current project state, phase scope |
| **Parser action** | Extract for context; do not duplicate into kernel files verbatim unless facts belong in memory |
| **Files updated** | None directly; may inform HANDOFF seed |
| **Use** | Orientation only; **CURRENT TASK** overrides for actionable work |

### 4.3 Section: PROJECT CONTEXT UPDATES

| Aspect | Specification |
|--------|---------------|
| **Content** | Product name, stack, database, constraints, layout, env notes |
| **Parser action** | Merge into existing `paws022/.ai/project_context.md`; preserve prior facts unless explicitly superseded |
| **Files updated** | `paws022/.ai/project_context.md` |
| **Bridge** | Sync project name into `main/.vedaws/project.toml` via **bridge.ingest_master_prompt** |
| **Rules** | Do not invent stack choices not stated here or in prior context |

### 4.4 Section: CURRENT TASK

| Aspect | Specification |
|--------|---------------|
| **Content** | `Status: in_progress`; H3 **Goal**; **Constraints**; **Acceptance criteria** (checkboxes); **Notes** |
| **Parser action** | Replace body of `current_task.md` with parsed task; set `Status: in_progress`; set **Started** date |
| **Files updated** | `paws022/tasks/current_task.md` |
| **Bridge** | Map Goal/phase to Vedaws software workflow task id (scope, architecture, api-design, implement, test, review, handoff); trigger state transition toward `planning` / `executing` |
| **Rules** | Exactly **one** primary goal per Master Prompt |

### 4.5 Section: BACKLOG ITEMS

| Aspect | Specification |
|--------|---------------|
| **Content** | Future phases; submission/documentation item **last** |
| **Parser action** | Append items to `paws022/tasks/backlog.md`; skip duplicates |
| **Files updated** | `paws022/tasks/backlog.md` |
| **Bridge** | Store ordered phase list in bridge manifest for workflow expectations |
| **Rules** | Do not implement backlog items in this run |

### 4.6 Section: EXECUTOR INSTRUCTIONS

| Aspect | Specification |
|--------|---------------|
| **Content** | Numbered list reinforcing PAWS duties |
| **Parser action** | Treat as binding constraints for this run; must not contradict Vespawd Executor Spec |
| **Files updated** | Indirect — drives which of architecture, db_schema, api_contracts, design, HANDOFF get touched |
| **Typical items** | Merge context; write current_task; update docs if needed; align UI with design; implement in userspace; update HANDOFF; summarize run/test |

If EXECUTOR INSTRUCTIONS conflict with CURRENT TASK acceptance criteria, **acceptance criteria win** for scope; note conflict in `current_task.md` Notes.

### 4.7 Parse failure

If any required H2 is missing or CURRENT TASK lacks Goal and Acceptance criteria:

1. Do **not** write userspace code.
2. List missing sections to the user.
3. Ask user to re-run Planner or paste a complete prompt.

---

## 5. Project Context Synchronization

### 5.1 Authority model

| Data | Authoritative store | Human-readable projection |
|------|---------------------|-------------------------|
| Orchestration state | `main/.vedaws/state.toml` | `paws022/tasks/status.md` |
| Active phase criteria | Parsed CURRENT TASK + `current_task.md` | Same file |
| Product facts | `paws022/.ai/project_context.md` | — |
| Workflow progress | `main/.vedaws/workflow-progress.json` | `current_task.md` + status |
| Transition history | `main/.vedaws/transitions.jsonl` | Optional; not edited by Executor |

Executor **writes PAWS projections**; Bridge **writes Vedaws**; Executor **never** hand-edits `.vedaws/`.

### 5.2 Synchronization matrix

| File | When updated | Updated by | Source of truth |
|------|--------------|------------|-----------------|
| `project_context.md` | Every Master Prompt ingest | Executor | PAWS memory |
| `current_task.md` | Ingest; progress log; blocked/complete | Executor; Bridge enriches task id | CURRENT TASK + Vedaws projection |
| `backlog.md` | Every Master Prompt ingest | Executor | Planner BACKLOG |
| `status.md` | After ingest, implement, complete, bridge sync | Executor via bridge.sync_status | Vedaws status + HANDOFF freshness + design gate |
| `HANDOFF_FOR_DOCUMENTER.md` | Ingest, implement complete, boundary changes | Executor | Aggregated facts |
| `main/.vedaws/*` | Bridge hooks only | Bridge / Vedaws CLI | Vedaws runtime |

### 5.3 Sync sequence (every Master Prompt)

```
1. Executor writes PAWS scheduler + context files (parse result)
2. bridge.ingest_master_prompt(parsed_sections)
3. bridge.sync_status() → refresh status.md
4. Executor seeds HANDOFF (facts from brief + context + task)
```

### 5.4 Sync sequence (after implementation)

```
1. Executor updates docs/api/schema if boundaries changed
2. bridge.post_phase_complete(task_outcome)
3. bridge.sync_status()
4. Executor refreshes HANDOFF
5. Executor appends tasks/completed/ if phase closed
```

### 5.5 Drift prevention

If `current_task.md` and `vedaws status --path main` disagree on active phase:

- **Vedaws orchestration wins** for eligibility (what may run next).
- Executor **rewrites** `current_task.md` Notes with Vedaws task id and blocker reason, or asks Planner for a corrective Master Prompt.
- Never silently ignore doctor failures.

---

## 6. Design Gate

Based on `paws022/docs/UI_DESIGN.md` and `paws022/design/DESIGN.md`.

### 6.1 When UI implementation is allowed

Executor may create or substantially change UI in userspace when **any** of:

| Condition | Details |
|-----------|---------|
| **A. Design ready** | `paws022/design/DESIGN.md` status is `ready for implementation` and current task screens are listed |
| **B. User override** | User explicitly says **skip design** or **design later** in chat for this task |
| **C. Non-UI work** | Task does not name screens, routes, or visual components |
| **D. Design-only phase** | CURRENT TASK is explicitly a design phase (update `design/` only, no `src/` UI) |

### 6.2 When Executor must refuse UI implementation

| Condition | Executor action |
|-----------|-----------------|
| Task names screens/UI and `DESIGN.md` is `not started` or `in progress` | Implement **non-UI** parts only; report design gate |
| Screens listed in DESIGN.md for this task but spec missing | Refuse UI; offer to update `design/DESIGN.md` first |
| bridge.pre_implement_check reports design_gate violation | Block; set `Status: blocked` |

### 6.3 How DESIGN.md affects execution

| DESIGN.md element | Executor behavior |
|-------------------|-------------------|
| **Status** | Gate control (see §6.1–6.2) |
| **Screens table** | Implement only listed screens for this phase; match routes/IDs |
| **Design system tokens** | Apply consistently in userspace |
| **sources.md** | Reference for assets; exports in `design/screens/`, `design/exports/` |
| **Implementation gate section** | Binding unless user override |

Optional: Executor may draft or merge **UI DESIGN BRIEF** content into `DESIGN.md` when tasked with design-only phase.

UI tool usage (Stitch, Figma exports, MCP) is **executor-side and optional**; artifacts must land in `paws022/design/` before UI code.

---

## 7. Code Implementation Rules

Inherited from `paws022/.ai/executor_rules.md`, `architecture_rules.md`, `coding_rules.md`.

### 7.1 Allowed directories

| Directory | Purpose |
|-----------|---------|
| `main/src/` | Application implementation (Vespawd sidecar userspace) |
| `main/docs/` | App technical docs mirrored per architecture (architecture/, api/, decisions/, handoff/) |
| `paws022/docs/` | PAWS memory (architecture.md, api_contracts.md, db_schema.md, decisions.md, HANDOFF) |
| `paws022/design/` | UI specs and exports |
| `paws022/tasks/` | Scheduler files |
| `paws022/.ai/project_context.md` | Product memory only |

Integrated layout (non-sidecar): userspace is `src/` at POS root per `project_context.md`.

### 7.2 Forbidden directories

| Directory | Rule |
|-----------|------|
| `paws022/.ai/` except `project_context.md` | Kernel — no edits |
| `paws022/src/` | Wrong userspace in sidecar layout |
| `vedaws/` | Frozen reference — read only |
| `main/.vedaws/` | Runtime-managed — Bridge only |
| `paws022/` POS kernel prompts | Do not modify planner/documenter prompts |

### 7.3 Minimal diff philosophy

- Change only what acceptance criteria require.
- Match existing naming, formatting, imports in touched files.
- No unrelated refactors, renames, or drive-by cleanup.
- One hypothesis per bugfix (`debugging_protocol.md`).

### 7.4 Architecture preservation

- Respect layers in `architecture_rules.md`: presentation → application → domain ← infrastructure.
- No business logic in thin handlers.
- No circular module dependencies.
- Public API changes → update `paws022/docs/api_contracts.md` in same effort.
- Schema changes → update `paws022/docs/db_schema.md`; ADR in `decisions.md` if non-trivial.

### 7.5 Documentation updates

| Change type | Required doc update |
|-------------|---------------------|
| New/changed API | `api_contracts.md` + mirror `main/docs/api/API.md` when bridge mirrors |
| Schema | `db_schema.md` |
| Structural decision | `decisions.md` |
| Architecture component | `architecture.md` |

### 7.6 Technical debt

- Record known debt in `current_task.md` Notes or `decisions.md`; do not fix unless task includes it.
- Do not add TODO comments without task linkage.

### 7.7 Refactors

- **Forbidden** unless CURRENT TASK explicitly authorizes or blocking bug requires minimal structural fix.
- If refactor is necessary, document scope in Notes before proceeding.

---

## 8. Bridge Integration

Bridge lives in `main/bridge/`. Executor invokes **operations**, not internal bridge code.

### 8.1 Invocation matrix

| Lifecycle point | Bridge operation | Executor action |
|-----------------|------------------|-----------------|
| First run / missing `.vedaws/` | `bootstrap` | Before parse writes |
| After successful parse | `ingest_master_prompt` | After PAWS scheduler writes |
| Before userspace edits | `pre_implement_check` | After sync; before §7 work |
| After implementation | `post_implement` (if distinct) | Optional telemetry |
| Acceptance met | `post_phase_complete` | Before final HANDOFF |
| Handoff phase | `pre_documenter` | Artifact checklist |
| Any status refresh | `sync_status` | After major steps |

### 8.2 Before implementation

`pre_implement_check` must validate:

- Design gate (§6)
- `vedaws doctor --path main` non-blocking (or documented waivers)
- Project state allows `executing` (or equivalent)
- Current workflow task matches parsed phase

**On failure:** do not edit `main/src/`; report blockers.

### 8.3 After implementation

- Record files changed summary in `current_task.md` Progress Log.
- Invoke bridge post hooks so Vedaws task progress and automation can run (e.g. git status after implement per software plugin rules).

### 8.4 After task completion

`post_phase_complete` with:

- Task id (Vedaws software.*)
- Outcome: completed | failed | blocked
- Acceptance criteria snapshot

Triggers: workflow task completion, optional `vedaws run --path main`, automation rules.

### 8.5 Before handoff

`pre_documenter`:

- Run `vedaws software artifacts --path main`
- Ensure HANDOFF sections populated
- Mark handoff workflow task complete when criteria met

---

## 9. Vedaws Integration

Executor communicates with Vedaws **only via CLI subprocess** targeting `main/`. No imports from `vedaws/` Python packages in userspace code.

### 9.1 Commands the Executor may invoke

| Command | Purpose |
|---------|---------|
| `vedaws init --template software --name <name>` | First-time project (bootstrap) |
| `vedaws doctor --path main` | Health gate |
| `vedaws status --path main` | Orchestration snapshot for status.md |
| `vedaws workflow show --path main` | Phase progress |
| `vedaws workflow activate software --path main` | Activate software workflow (bootstrap) |
| `vedaws run --path main` | Advance dispatch loop after implementation |
| `vedaws tasks complete <workflow.task> --path main` | Record completion when bridge does not |
| `vedaws software artifacts --path main` | Doc artifact checklist |
| `vedaws state transition <state> --path main` | Only when architecture prescribes; prefer bridge |

Executor **must not** instruct users to edit `.vedaws/*.toml` or `workflow-progress.json`.

### 9.2 Workflow activation

- Software workflow id: `software` (`vedaws/plugins/software/templates/project/workflows/software.workflow.toml`).
- Activated during bootstrap or first `ingest_master_prompt`.
- Executor maps CURRENT TASK to task ids: `scope`, `architecture`, `api-design`, `implement`, `test`, `review`, `handoff`.

### 9.3 State transitions

Executor does not manage state machine directly except via bridge/CLI.

Typical transitions (driven by bridge):

| Event | State direction |
|-------|-----------------|
| Master Prompt ingested | toward `planning` / `executing` |
| Implementation starts | `executing` |
| Phase awaits human test | `awaiting_approval` (optional) |
| Blocked | `blocked` |
| Handoff complete | toward `completed` |

### 9.4 Doctor checks

Run when:

- `pre_implement_check` runs
- User reports stuck state
- Handoff phase begins

Report doctor output summarised in chat; set `Status: blocked` on hard failures.

### 9.5 Workflow progress

After work, Executor may cite `vedaws workflow show --path main` in summary so user sees phase alignment without reading JSON.

### 9.6 Automation triggers

Executor does not author automation rules. Software plugin may trigger actions on `TaskCompleted` (e.g. `git.status`). Executor surfaces subprocess results if returned to chat.

---

## 10. Task Completion

A phase is **complete** when **all** of the following hold:

### 10.1 Acceptance criteria

- Every checkbox in CURRENT TASK / `current_task.md` is satisfied or explicitly deferred with user approval in Notes.
- Deferred items recorded in HANDOFF **Features not implemented**.

### 10.2 Testing

- Executor runs applicable tests or documents manual test steps.
- Test commands recorded in HANDOFF **Testing / demo**.
- Executor does not claim tests passed without evidence (command output or explicit user confirmation).

### 10.3 Documentation

- Boundary changes reflected in api/schema/architecture/decisions per §7.5.
- HANDOFF refreshed (§13).

### 10.4 Bridge synchronization

- `post_phase_complete` succeeded or failure recorded.
- `sync_status` updated `status.md`.

### 10.5 Orchestration updates

- Vedaws workflow task for this phase marked completed (via bridge or `vedaws tasks complete`).
- `vedaws doctor --path main` has no unacknowledged blockers.

### 10.6 Close-out writes

| Artifact | Action |
|----------|--------|
| `current_task.md` | `Status: idle` or await next prompt; Progress Log entry |
| `tasks/completed/YYYY-MM-DD-slug.md` | Create summary log |
| `backlog.md` | Do not remove items; Planner manages on next prompt |

### 10.7 Executor report to user

Must include:

- What changed (files/features)
- How to run and test
- Whether HANDOFF is current
- **Next suggested action:** human test → Planner follow-up, or small fix in Executor chat
- If handoff-ready: *Submission handoff is ready for your documenter + rubric.*

---

## 11. Failure Handling

### 11.1 Planner omitted information

| Situation | Behavior |
|-----------|----------|
| Missing required section | Refuse implement; list gaps (§4.7) |
| Vague acceptance criteria | Ask user one clarifying question; if still vague, write testable criteria to Notes and proceed minimally |
| Missing stack/DB | Infer only from `project_context.md`; do not invent MySQL if context says otherwise |

### 11.2 Design missing

| Situation | Behavior |
|-----------|----------|
| UI task, design not ready | Non-UI only + blocked UI with reason |
| User says skip design | Document override in Notes; proceed |

### 11.3 Dependencies fail

| Situation | Behavior |
|-----------|----------|
| npm/pip/composer install fails | `Status: blocked`; capture error; debugging_protocol |
| DB unreachable | Block; verify `project_context.md` + env |
| Missing env vars | List required vars; no fake values |

### 11.4 Implementation blocked

| Situation | Behavior |
|-----------|----------|
| Scope exceeds single phase | Complete in-phase portion; backlog remainder |
| External API unavailable | Mock only if task allows; else block |

### 11.5 Orchestration fails

| Situation | Behavior |
|-----------|----------|
| `vedaws` CLI missing | PAWS file sync still proceeds; warn orchestration offline |
| doctor fails | `Status: blocked`; show doctor output |
| bridge hook errors | Complete PAWS work if safe; record orchestration error in Notes |

### 11.6 Acceptance criteria cannot be satisfied

1. Implement partial deliverable if valuable.
2. Mark unmet criteria in Notes and HANDOFF **Features not implemented**.
3. Set `Status: blocked` or leave `in_progress` with clear reason.
4. Do not mark phase complete or tell user to go to Planner without stating gaps.

---

## 12. Recovery Workflow

### 12.1 Resume after blocked task

```
1. Human addresses blocker (design, env, doctor, deps)
2. User confirms in Executor chat OR pastes fix instructions
3. Executor updates current_task.md (Status: in_progress)
4. bridge.pre_implement_check
5. Continue implementation or re-run failed step
6. Normal completion flow (§10)
```

### 12.2 Resume after failed orchestration

```
1. Executor records last successful PAWS state
2. User or maintainer fixes Vedaws install / main/.vedaws integrity
3. vedaws doctor --path main → pass
4. bridge.sync_status
5. Executor continues from current_task.md — no duplicate PAWS writes unless re-ingesting prompt
```

### 12.3 Resume mid-phase (new chat session)

Executor **must** read `current_task.md`, `status.md`, `project_context.md` before any code. Do not restart from Master Prompt unless user re-pastes it.

### 12.4 Re-ingest Master Prompt

If user re-pastes same or superseding prompt:

- Overwrite `current_task.md` per new CURRENT TASK.
- Re-run ingest + sync.
- Do not duplicate backlog items.

### 12.5 Debugging loop

Follow `paws022/.ai/debugging_protocol.md`. Update Progress Log with what was tried. Small fixes stay in Executor chat without new Planner prompt.

---

## 13. Handoff Behavior

`paws022/docs/HANDOFF_FOR_DOCUMENTER.md` is the **documenter-facing** handoff. Mirror facts may copy to `main/docs/handoff/HANDOFF.md` via bridge for Vedaws artifact checks.

### 13.1 When to update

| Trigger | Update HANDOFF |
|---------|----------------|
| Master Prompt ingested | Seed project name, stack, phase goals |
| Task / phase completes | Features, run instructions, limitations |
| `main/src/` or schema/API changes | What was built, how to run |
| User says feature-complete | Full refresh |
| Before documenter phase | Final pass + rubric checklist |

### 13.2 Required facts (sections)

Per template (`paws022/docs/HANDOFF_FOR_DOCUMENTER.md`):

| Section | Content |
|---------|---------|
| Project | Name, course, team |
| What was built | Factual bullet summary |
| How to run | Commands in fenced block |
| Tech stack | Table from project_context |
| UI / design | DESIGN.md status, sources, screens built |
| Features implemented | Checklist |
| Features not implemented | Honest list |
| Testing / demo | Numbered steps |
| Known limitations | Bullets |
| Rubric checklist | Checkboxes from rubric when known |
| Footer | `Generated: YYYY-MM-DD HH:mm:ss` and repo path |

### 13.3 Sources to pull from

`project_context.md`, `current_task.md`, completed tasks, `architecture.md`, `db_schema.md`, `api_contracts.md`, `main/src/` tree, `design/DESIGN.md`.

### 13.4 What must never appear in HANDOFF

| Forbidden | Reason |
|-----------|--------|
| Submission report prose (introduction, conclusion essay) | Documenter role |
| Invented features or test results | Factual integrity |
| POS MASTER PROMPT text | Planner artifact |
| Vedaws internals, CLI dumps (full) | User-facing doc noise |
| Secrets, tokens, passwords | Security |
| Speculation about grading | Documenter + rubric |

### 13.5 Handoff-ready signal

When HANDOFF is current and implementation phases complete, Executor states:

> *Submission handoff is ready for your documenter + rubric.*

---

## 14. Tool Neutrality

This specification is **binding for all Executor implementations**.

| Requirement | Detail |
|-------------|--------|
| Terminology | Use **Executor**, not vendor IDE names |
| Rules source | `paws022/.ai/executor_rules.md` + this spec |
| IDE integration | Cursor: `.cursor/rules/`; others: `AGENTS.md` + pasted executor rules |
| UI tools | Optional MCP/export; artifacts in `design/` |
| Planner | Any external chat producing POS MASTER PROMPT |
| Vedaws | CLI subprocess only; Python install is environment prep, not Executor identity |

An Executor implementation **must not** require features exclusive to one IDE (e.g. a single-vendor MCP) to satisfy core acceptance criteria. UI MCP is optional enhancement.

Compatibility test: an Executor following this spec must produce the same PAWS file mutations and bridge invocations whether running in Windsurf, VS Code, JetBrains AI, or any future agent.

---

## 15. Design Goals

This specification prioritizes:

| Goal | How the spec enforces it |
|------|--------------------------|
| **Deterministic behavior** | Fixed parse order, startup before code, explicit gates |
| **Minimal hallucination** | No invented features/secrets; HANDOFF facts only |
| **Predictable execution** | Lifecycle §2; completion criteria §10 |
| **Resumable execution** | Read current_task on session resume §12.3 |
| **Project consistency** | Sync matrix §5; Vedaws authority for eligibility |
| **Maintainability** | Minimal diff §7.3; ADRs for decisions |
| **PAWS compatibility** | Same Master Prompt format, file paths, handoff rules |
| **Vedaws compatibility** | CLI integration §9; no `.vedaws` hand edits |

---

## Appendix A — Quick reference checklist

Executor runs this mentally on every Master Prompt:

- [ ] Recognize POS MASTER PROMPT
- [ ] Startup read order complete
- [ ] Parse all H2 sections
- [ ] Write project_context, current_task, backlog
- [ ] bridge.ingest_master_prompt + sync_status
- [ ] Seed HANDOFF
- [ ] bridge.pre_implement_check (design + doctor)
- [ ] Implement userspace + docs only if gates pass
- [ ] Update api/schema/architecture if needed
- [ ] bridge.post_phase_complete + sync_status
- [ ] Refresh HANDOFF + completed log
- [ ] Report run/test + next action

---

## Appendix B — Related documents

| Document | Role |
|----------|------|
| [VESPAWD_ARCHITECTURE.md](VESPAWD_ARCHITECTURE.md) | System integration |
| [START_HERE.md](START_HERE.md) | User-facing workflow |
| [PAWS_VS_VEDAWS_ANALYSIS.md](PAWS_VS_VEDAWS_ANALYSIS.md) | Comparative analysis |
| `paws022/.ai/executor_rules.md` | PAWS baseline executor rules |
| `paws022/.ai/planner_prompt.md` | Master Prompt format |
| `paws022/docs/UI_DESIGN.md` | Design gate contract |

---

*Canonical Vespawd Executor Specification. Design only — no implementation.*
