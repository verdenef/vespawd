# Planner ↔ executor loop (POS v1.1.0)

## Roles

| Role | Job | Output |
|------|-----|--------|
| **Planner** (e.g. planner (external)) | Plan only | `# POS MASTER PROMPT` |
| **Executor** (e.g. Cursor) | Task files + code | `tasks/current_task.md`, `src/`, HANDOFF |

Planner never outputs code. Executor never requires manual `current_task.md` on first paste.

---

## Cycle

```
pos-new → open app in executor IDE
Planner → POS MASTER PROMPT → executor "Execute this."
Test → small fix? stay in executor
Next phase? Planner follow-up → new POS MASTER PROMPT
Done? Documenter + HANDOFF + rubric
```

---

## After the first Master Prompt

1. Executor updates memory, `current_task`, `src/`, HANDOFF, `status.md`.
2. You run/test.
3. Choose:

| Result | Next |
|--------|------|
| Small fix | Executor chat only |
| Phase 2+ | [.ai/planner_followup_message.md](../.ai/planner_followup_message.md) → Planner → paste new prompt |
| Submission report | documenter + HANDOFF (see [SUBMISSION_DOCUMENTATION.md](SUBMISSION_DOCUMENTATION.md)) |

Legacy prompts titled `CURSOR MASTER PROMPT` still work if executor rules include the alias.

---

## Submission (last)

Executor auto-maintains `docs/HANDOFF_FOR_DOCUMENTER.md`. Documenter writes prose; export via Canvas/Docs if needed.
