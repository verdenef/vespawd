# Coding Rules (POS Kernel)

Baseline standards for every repo using this template. **Project-specific** style (linters, formatters, frameworks) belongs in `project_context.md` or team docs linked from there.

## General

- Match existing naming, formatting, and import style in the file you edit.
- Scope changes to the active task; avoid unrelated refactors.
- Prefer clear code over comments; comment only non-obvious rationale.

## Style

- Meaningful names; avoid opaque abbreviations unless domain-standard.
- Small, focused functions; extract when logic becomes hard to follow.
- Handle errors explicitly; log or propagate—do not swallow silently.

## Data Stores

- Use the database engine declared in `project_context.md` and `docs/db_schema.md`.
- Parameterized queries only; never interpolate untrusted input into SQL.
- Canonical schema and migration notes live in `docs/db_schema.md`.

## Tests

- Add tests when requested or when they protect real, non-trivial behavior.
- Skip tests that only duplicate framework guarantees.

## Git

- No commits or pushes unless explicitly requested.

## Project Overrides

Team or repo-specific rules (e.g. “always use Zod for validation”) go in `project_context.md` under **Agent Notes**, not by forking this file for every new project unless the whole org adopts the change in the POS template.
