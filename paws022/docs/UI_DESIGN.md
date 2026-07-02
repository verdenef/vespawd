# UI design in POS (tool-neutral)

POS does **not** ship a built-in UI builder. It ships a **contract**: where design artifacts live and when the executor must read them before coding screens.

Any tool works if it ends up in `design/` (or linked from `design/sources.md`).

## Recommended approach: artifact contract + optional role

| Layer | What it is | Tool dependency |
|-------|------------|-----------------|
| **`design/` folder** | Source of truth for “what the UI should look like” | None — files + links |
| **Optional UI designer** | External agent (Gemini, ChatGPT, …) that fills `design/` | Your choice |
| **Executor** | Implements `src/` from `design/` + tasks | Any IDE; **MCP tools optional** (Stitch, etc.) |

We **recommend** tools that expose **MCP** (or clean export) so the executor can pull screens/code without copy-paste. **Google Stitch** is a strong default for Cursor users — not required.

### Why not “Stitch-only” or a 4th mandatory role?

- Classmates use Figma, Penpot, v0, screenshots, or no design phase.
- POS stays **tool-neutral** like planner/executor/documenter.
- A mandatory “Designer” role adds setup friction for API-only projects.

Use a **design phase** only when the app has meaningful UI.

## Pipeline (UI-heavy projects)

```text
Assignment
  → Planner → POS MASTER PROMPT (may include UI phase in backlog)
  → [Optional] UI designer → updates design/DESIGN.md + design/sources.md (+ exports)
  → Executor → read design/ → implement src/ → HANDOFF
  → Documenter (last)
```

**Design-before-code gate (default for new screens):** If `design/DESIGN.md` or `design/sources.md` lists screens for the current task, executor implements to match those artifacts — or user explicitly says **skip design** / **design later**.

## `design/` contract

| Path | Purpose |
|------|---------|
| [design/README.md](../design/README.md) | How this folder works |
| `design/DESIGN.md` | Design system + screen list + acceptance notes (human or agent) |
| `design/sources.md` | Links: Figma, Stitch project, Penpot, v0 chat, etc. |
| `design/screens/` | Exported PNG/SVG/HTML snippets (optional) |
| `design/exports/` | Tool dumps (Stitch HTML, etc.) — gitignore large binaries if needed |

Executor and planner both reference **`design/DESIGN.md`**, not a vendor URL buried in chat.

## Tool options (pick one or combine)

| Tool | How it fits POS | MCP? |
|------|-----------------|------|
| **Google Stitch** | Generate screens → export to `design/exports/` or fetch via Stitch MCP in **executor** chat | Yes (community servers) |
| **Figma** | Link file in `sources.md`; export frames to `design/screens/` | Some third-party MCPs |
| **v0 / Lovable / similar** | Paste export or link in `sources.md` | Varies |
| **Penpot / Lunacy** | Open source; export assets to `design/screens/` | Rare |
| **Manual** | Write `DESIGN.md` + screenshots only | N/A |
| **Executor only** | Skip external designer; user describes UI in Master Prompt; executor drafts `design/DESIGN.md` then codes | Executor’s MCPs |

**Recommendation:** For Cursor + visual apps, use **Stitch (or any MCP UI tool)** in the **executor** step, then **commit** the resulting `design/` artifacts so the repo stays the source of truth — not the cloud tool alone.

## Optional external “UI designer”

Copy [.ai/ui_designer_prompt.md](../.ai/ui_designer_prompt.md) into a Gem/GPT (same pattern as planner/documenter). Output is a **UI DESIGN BRIEF** (updates `design/DESIGN.md` content), **not** a POS MASTER PROMPT.

Typical flow:

1. Planner backlog: “UI: auth + dashboard (see design/)”
2. You run UI designer with assignment + rough ideas → paste result into `design/DESIGN.md` or ask executor to merge it
3. Executor phase: implement screens listed in `design/DESIGN.md`

## Google Stitch + Cursor (recommended for many students)

**Quick guide:** [STITCH_CURSOR.md](STITCH_CURSOR.md) — setup from stitch.withgoogle.com (often **no Google Cloud**), where to type prompts, backend-first order.

**Planner does not write Stitch prompts** — only screen names/phases. **Executor chat** asks Stitch via MCP.

Executor chat pattern:

```text
Read design/DESIGN.md. Using Stitch MCP, generate [screen name] to match DESIGN.md, save exports under design/exports/, then implement in src/.
```

Config template: [.cursor/mcp.json.example](../.cursor/mcp.json.example) → copy to `.cursor/mcp.json` in your **app** repo (gitignored).

**Legacy / alternate MCP** (only if your package README requires it): `GOOGLE_CLOUD_PROJECT` + `gcloud` — see community package docs.

Other MCP UI tools: same pattern — **artifact lands in `design/`**, then code.

## Planner / executor hooks

- **Planner:** For UI work, backlog item names screens; point to `design/`; Phase 1 can be “design only” before `src/` UI.
- **Executor:** See [.ai/executor_rules.md](../.ai/executor_rules.md) — read `design/` before new UI in `src/`.
- **HANDOFF:** UI summary for documenter (see `docs/HANDOFF_FOR_DOCUMENTER.md`).

## Config (optional)

`~/.pos/config.json` may include:

```json
"toolchain": {
  "planner": "gemini-gem",
  "executor": "cursor",
  "documenter": "gemini-gem",
  "uiDesigner": "none"
}
```

Values: `none` | `external` | `executor` (executor = you use IDE + MCP, no separate Gem).

## Alternatives we considered

| Approach | Verdict |
|----------|---------|
| Built-in POS UI builder | Out of scope — POS is workflow, not a product |
| Stitch baked into template | Too vendor-specific |
| Mandatory 4th role “Designer” | Too heavy for non-UI projects |
| **Artifact contract `design/`** | **Adopted** — tool-neutral, works with any export |
| Design only in chat | Fragile — not in repo memory |
| Figma-only docs | Excludes Stitch/MCP-first users |

## See also

- [STITCH_CURSOR.md](STITCH_CURSOR.md) — Stitch + Cursor quick guide
- [design/examples/ml-bi.DESIGN.md](../design/examples/ml-bi.DESIGN.md) — sample screens for ML/BI finals
- [LAZY_WORKFLOW.md](LAZY_WORKFLOW.md)
- [TOOLCHAIN.md](TOOLCHAIN.md)
- [EXTERNAL_AGENTS_SETUP.md](EXTERNAL_AGENTS_SETUP.md)
