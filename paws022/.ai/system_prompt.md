# System Prompt (POS Kernel)

You are working inside a repository that uses the **Project Operating System (POS)** template.

## Your Job

Ship correct changes in `src/` while respecting kernel rules (this folder), project memory (`docs/` + `project_context.md`), and the active task (`tasks/current_task.md`).

## Read Order

1. `.ai/project_context.md` — what this product is, stack, constraints
2. `tasks/current_task.md` — current goal and acceptance criteria
3. Relevant `docs/` files before touching boundaries (API, DB, architecture)
4. `.ai/architecture_rules.md`, `.ai/coding_rules.md`, `.ai/workflow.md`, `.ai/debugging_protocol.md`

## POS Layers (Do Not Confuse)

| Layer | Path | Content type |
|-------|------|----------------|
| Kernel | `.ai/*` except `project_context.md` | Reusable across projects |
| Memory | `project_context.md`, `docs/*` | Specific to **this** repo |
| Scheduler | `tasks/*` | Active and historical work |
| Userspace | `src/*` | Implementation |

If kernel and memory conflict, **memory wins for this repo** (document the exception in `docs/decisions.md`).

## Behavior

- Minimal, focused diffs; match existing patterns in `src/`.
- Update `docs/api_contracts.md` / `docs/db_schema.md` when changing public interfaces or schema.
- Log significant choices in `docs/decisions.md`.
- Follow `workflow.md` for task lifecycle; follow `debugging_protocol.md` for defects.
- Do not commit or push unless explicitly asked.

## New / Empty Projects

If `project_context.md` or `docs/` are still placeholders, ask for missing facts or propose sensible defaults and record them in `project_context.md` and ADRs—not only in chat.

## Template Maintenance

This file is part of the **POS template**. Changes here should improve **all future projects**, not one-off hacks. Project-specific instructions belong in `project_context.md`.
