# Lazy workflow (POS v1.1.7)

You provide ideas; the **planner** writes `POS MASTER PROMPT`; the **executor** updates tasks and `src/`.

## Pipeline

```
Assignment → Planner (e.g. planner (external))
    → POS MASTER PROMPT
    → [Optional] UI designer → design/DESIGN.md  (see UI_DESIGN.md)
    → Executor IDE (e.g. Cursor; optional UI MCP e.g. Stitch)
    → HANDOFF auto-updated
    → Documenter (last) + rubric
```

UI-heavy apps: see [UI_DESIGN.md](UI_DESIGN.md). API-only: skip `design/` work.

## Steps

| Step | Action |
|------|--------|
| 0 | [START.md](../START.md) — setup once |
| 1 | `pos-new my-app` → open app folder in executor |
| 2 | Planner → copy **POS MASTER PROMPT** |
| 3 | Executor chat: `Execute this.` + paste |
| 4 | Test; small fixes in executor only |
| 5 | Next phase → [.ai/planner_followup_message.md](../.ai/planner_followup_message.md) |

See [EXECUTOR_LOOP.md](EXECUTOR_LOOP.md) for after the first prompt.

## Folders

| Path | Role |
|------|------|
| Template clone | Edit template / maintain POS |
| `{{PROJECTS_DIR}}/my-app` | Real project work |

Legacy `CURSOR MASTER PROMPT` still accepted by executor rules during transition.
