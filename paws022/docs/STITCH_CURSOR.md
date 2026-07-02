# Google Stitch + Cursor (quick guide)

POS does **not** install Stitch. You connect it in **Cursor** and ask for UI in **executor chat** — same chat as backend work.

**Planner Gem does not run Stitch** and does not need Stitch-style prompts. See [UI_DESIGN.md](UI_DESIGN.md).

## Setup (most users — no Google Cloud)

1. Open [stitch.withgoogle.com](https://stitch.withgoogle.com/) and sign in.
2. Use Stitch’s **MCP** or **Connect to Cursor** flow — copy the JSON it gives you.
3. **Cursor → Settings → MCP → Add server** — paste that config (or merge into project `.cursor/mcp.json`).
4. Restart Cursor if needed. MCP panel should show **stitch** connected.
5. Test in chat: `List my Stitch projects.`

If Stitch gave you an **API key** env var, use their exact JSON — do not mix with older guides that only mention `gcloud`.

### Optional: Google Cloud path

Some community MCP packages use `GOOGLE_CLOUD_PROJECT` + `gcloud auth application-default login`. Only follow that if **your** MCP README requires it. See [UI_DESIGN.md](UI_DESIGN.md) for an example.

### Example config (template only — copy to `.cursor/mcp.json`, fill secrets locally)

See [.cursor/mcp.json.example](../.cursor/mcp.json.example). **Do not commit** real keys.

## Where you “prompt” Stitch

**Only in Cursor chat** (executor), e.g.:

```text
Use Stitch MCP to create a Data Upload screen for a Dogecoin ML BI app:
CSV file picker, preview table, Import button, clean academic light theme.
Save HTML to design/exports/s1-upload.html and update design/DESIGN.md.
```

You do **not** need a new chat for UI (optional if context is messy).

## Suggested order (ML / data apps)

| Step | Where | What |
|------|--------|------|
| 1 | Planner Gem | Phase 1–3: data, features, models — **no Stitch** |
| 2 | Cursor | Backend until ingest + at least one model works |
| 3 | Cursor | Stitch for screens; wire to API |
| 4 | Documenter Gem | Report; use `design/screens/` or HANDOFF for figures |

## Consistent multi-screen flow

1. Generate **first** screen (e.g. home / upload).
2. `Extract design context` from that screen (wording depends on MCP tools).
3. Generate next screens “using same design context.”
4. `fetch_screen_code` → `design/exports/` → implement in `src/`.

## POS files to touch

| File | Purpose |
|------|---------|
| `design/DESIGN.md` | Screen list + status |
| `design/sources.md` | Stitch project URL, MCP package name, auth note |
| `design/exports/` | HTML from Stitch |
| `design/screens/` | PNG screenshots (report / demo) |

## Example `design/sources.md` line

```markdown
| Google Stitch | https://stitch.withgoogle.com/... | MCP in Cursor via Stitch site setup (API key); project "IS108-DOGE-BI" |
```

## Troubleshooting

| Problem | Try |
|---------|-----|
| MCP not listed | Re-paste config; restart Cursor |
| Tools never called | Say explicitly: “Use Stitch MCP” |
| HTML only, app broken | Normal — you wire Stitch HTML to your framework/API |
| Auth errors | Re-run Stitch connect flow; check env vars in MCP config |

## See also

- [UI_DESIGN.md](UI_DESIGN.md) — tool-neutral design folder
- [design/examples/ml-bi.DESIGN.md](../design/examples/ml-bi.DESIGN.md) — sample screen list for BI/ML finals
