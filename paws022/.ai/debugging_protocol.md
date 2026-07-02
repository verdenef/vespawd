# Debugging Protocol (POS Kernel)

Same investigation process for every POS-backed project. **Environment-specific** commands belong in `project_context.md`.

## 1. Reproduce

- Exact steps, inputs, branch, config.
- Verbatim errors, stack traces, status codes.

## 2. Isolate

- Which layer fails (presentation, application, domain, infrastructure).
- One variable at a time; minimal reproducers.
- No shotgun changes across unrelated modules.

## 3. Hypothesize

- One hypothesis per iteration.
- Evidence first: logs, traces, queries, network—not guesses.

## 4. Fix

- Smallest change that fixes root cause.
- No opportunistic refactors during hotfix unless required.

## 5. Verify

- Original repro steps pass.
- Sensible regression checks on adjacent paths.
- Note resolution in `tasks/current_task.md` or a new `tasks/completed/` entry.

## Data Layer

- Confirm engine and connection settings match `project_context.md`.
- Compare live schema to `docs/db_schema.md`.
- Use EXPLAIN / profiling appropriate to your engine for performance issues.

## When Stuck

Update `tasks/current_task.md` with:

- What was tried
- What each attempt proved
- Open questions for a human
