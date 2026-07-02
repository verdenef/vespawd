# Workflow (POS Kernel)

## Bootstrap

See [BOOTSTRAP.md](../BOOTSTRAP.md) or [START.md](../START.md). Prefer `setup/wizard.html` / `pos-setup.ps1`.

## Starting work

1. `tasks/current_task.md`
2. `tasks/status.md`
3. `.ai/project_context.md` + relevant `docs/`
4. Implement in `src/`

## Finishing work

1. Summarize and verify.
2. `tasks/completed/YYYY-MM-DD-slug.md`
3. Update `docs/HANDOFF_FOR_DOCUMENTER.md`
4. Update `tasks/status.md`
5. Reset `current_task` or pull from backlog
6. ADR in `docs/decisions.md` if architectural

## Lazy intake

Paste **POS MASTER PROMPT** (or legacy CURSOR alias). See [docs/LAZY_WORKFLOW.md](../docs/LAZY_WORKFLOW.md).

## Agents

No Master Prompt and empty task → read `tasks/intake.md` or ask once; do not invent large scope.
