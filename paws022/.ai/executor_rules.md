# Executor rules (POS)

Tool-neutral rules for the **coding agent** (Cursor, Copilot, Windsurf, etc.) in a POS-backed repository.

Cursor users: also loaded via `.cursor/rules/pos.mdc`. Other IDEs: paste this file or use root `AGENTS.md`.

## Read order

1. `.ai/project_context.md` — product, stack, constraints
2. `tasks/current_task.md` — active goal and acceptance criteria
3. `tasks/status.md` — phase snapshot (if present)
4. Relevant `docs/` before boundary changes (architecture, api_contracts, db_schema)
5. `design/DESIGN.md` and `design/sources.md` before **new or changed UI** in userspace (see `docs/UI_DESIGN.md`)
6. `.ai/system_prompt.md`, then architecture_rules, coding_rules, workflow, debugging_protocol as needed

## Layers

| Layer | Path | Edit when |
|-------|------|-----------|
| Kernel | `.ai/` except `project_context.md` | Template/org updates only |
| Memory | `project_context.md`, `docs/` | This project's facts |
| Scheduler | `tasks/` | Work lifecycle |
| Userspace | `src/` or sidecar app folder (see below) | Implementation |

If kernel and memory conflict, **memory wins**; note exceptions in `docs/decisions.md`.

### Sidecar layout

If `.ai/project_context.md` lists **Mode: sidecar**, the POS kernel lives under **`paws022/`**. Implement application code under the **Application code** path from project context (never `paws022/src/`).

**Vespawd projects** nest the kernel one level deeper. The user opens the **project root** in the IDE, where:

- POS memory is at `vespawd/paws022/` (`.ai/`, `tasks/`, `docs/`, `design/`)
- Application code is at `main/src/` (sibling of `vespawd/`; `Application code` resolves to `../../main/src`)
- The executor CLI runs with `--workspace vespawd/` (there is no single folder that is the direct parent of both `paws022/` and `main/`; the Bridge resolves paths from `main/bridge/manifest.toml`)
- `vespawd/vedaws/` and `vespawd/main/.vedaws/` are orchestration state — **managed automatically, do not hand-edit**

When paths in this file or a Master Prompt are written without the `vespawd/` prefix, prepend `vespawd/` to reach POS files from the project root. Legacy POS-only repos (no `vespawd/` folder) use the paths as written.

## While working

- One primary goal in `tasks/current_task.md`; backlog in `tasks/backlog.md`.
- API/schema changes → update `docs/api_contracts.md` / `docs/db_schema.md` same effort.
- Architectural choices → `docs/decisions.md`.
- Finished work → `tasks/completed/YYYY-MM-DD-slug.md`, reset or advance current task.
- Refresh `tasks/status.md` on phase complete (phase, app status, handoff freshness).
- **Always** refresh `docs/HANDOFF_FOR_DOCUMENTER.md` after meaningful work (see below).

## Master Prompt intake

When the user pastes **`# POS MASTER PROMPT`** or legacy **`# CURSOR MASTER PROMPT`** (or says "execute master prompt"):

Parse: PROJECT BRIEF, PROJECT CONTEXT UPDATES, CURRENT TASK, BACKLOG ITEMS, **EXECUTOR INSTRUCTIONS** (legacy: CURSOR INSTRUCTIONS).

**UI tasks:** If CURRENT TASK or acceptance criteria name screens/UI, read `design/DESIGN.md` first. If status is not `ready for implementation` and user did not say **skip design**, either update `design/` (including MCP exports to `design/exports/`) or implement only non-UI parts of the task.

1. Write `tasks/current_task.md` from CURRENT TASK (`Status: in_progress`).
2. Merge PROJECT CONTEXT UPDATES into `.ai/project_context.md`.
3. Append BACKLOG ITEMS to `tasks/backlog.md` (no duplicates).
4. Seed/update `docs/HANDOFF_FOR_DOCUMENTER.md` (facts only).
5. Implement in userspace (`src/` or sidecar app path from project_context) per acceptance criteria.
6. Update HANDOFF again after implementation.
7. Update `tasks/status.md`.

Do not ask the user to edit task files manually first.

Short natural-language tasks without a Master Prompt: still write `current_task.md` before coding.

## Adopt bootstrap (existing repos)

When the user pastes **`# POS ADOPT BOOTSTRAP`** (from `docs/ADOPT_BOOTSTRAP_PROMPT.md` after `pos-adopt.ps1`):

Fill POS memory from the repository per that prompt. Do not implement features or edit userspace code except to read/analyze. Merge with existing `project_context.md` content when present.

## Handoff automation

Maintain `docs/HANDOFF_FOR_DOCUMENTER.md` automatically — factual bullets only, no report prose.

Update when: Master Prompt completes; task completes; `src/` or schema/API docs change; user says feature-complete.

Pull from: project_context, current_task, completed tasks, architecture, db_schema, api_contracts, `src/` tree. Footer: `Generated: YYYY-MM-DD HH:mm:ss` and repo path.

School reports → user's **documenter** tool (e.g. documenter (external)), not long prose here.

When current, say: *Submission handoff is ready for your documenter + rubric.*

## Defaults

- Minimal diffs; match existing `src/` patterns.
- No git commit/push unless explicitly requested.
- Database per `project_context.md` and `docs/db_schema.md`.

See `docs/LAZY_WORKFLOW.md`, `docs/EXECUTOR_LOOP.md`, `docs/UI_DESIGN.md`.
