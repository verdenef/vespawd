# Design artifacts (POS)

Tool-neutral folder. **Executor** reads this before implementing new UI in `src/`.

## Files

| File | Required | Purpose |
|------|----------|---------|
| `DESIGN.md` | For UI phases | Screens, layout rules, colors, typography, component notes |
| `sources.md` | Recommended | Links to Figma, Stitch, Penpot, v0, etc. |
| `screens/` | Optional | Exported PNG/SVG per screen |
| `exports/` | Optional | HTML or tool dumps (e.g. Stitch export) |

## Workflow

1. Fill `DESIGN.md` (manually, UI designer agent, or executor after Stitch/MCP).
2. Record tool links in `sources.md`.
3. Export assets into `screens/` or `exports/` when your tool allows.
4. Planner/executor tasks reference screen **names** listed in `DESIGN.md`.

## Skip design

API-only or CLI projects can leave this folder minimal. Say **skip design** in the executor chat if there is no UI work.

See [docs/UI_DESIGN.md](../docs/UI_DESIGN.md) · [docs/STITCH_CURSOR.md](../docs/STITCH_CURSOR.md) · [examples/ml-bi.DESIGN.md](examples/ml-bi.DESIGN.md) (ML/BI sample).
