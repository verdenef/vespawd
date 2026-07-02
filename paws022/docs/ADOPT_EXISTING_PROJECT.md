# Add POS to an existing project

Use this when you already have code (e.g. CSC midterm) and want POS **without** starting over.

## What changes (and what does not)

| Action | Happens? |
|--------|----------|
| Adds `.ai/`, `tasks/`, POS `docs/`, Cursor rules | Yes |
| Updates `executor_rules.md` via sync | Yes |
| Deletes or moves your `src/` | **No** |
| Overwrites `project_context.md` if you already have one | **No** |
| Replaces your README | **No** |
| Auto-reads your codebase during `pos-adopt` | **No** — use bootstrap chat below |

**Recommended:** let the script create a **full-folder backup** first (default). Restore by copying the backup folder back if anything feels wrong.

## How to run

From your **template clone** (paws022):

```powershell
.\scripts\pos-adopt.ps1 -TargetPath "C:\path\to\your-existing-project"
```

Prompts for backup unless you pass `-SkipBackup`.

## Fill POS memory from your project (paste prompt)

`pos-adopt` only adds **skeleton** markdown (folder name, MySQL default, `_TBD_` fields). It does **not** scan `src/` for you.

After adoption:

1. Open the **adopted project** in your executor IDE (Cursor, etc.).
2. Open **[ADOPT_BOOTSTRAP_PROMPT.md](ADOPT_BOOTSTRAP_PROMPT.md)**.
3. Copy everything **below the `---` line** (the USER REQUEST + EXECUTOR INSTRUCTIONS block).
4. Paste into a **new chat** and send (no extra preamble needed).

The executor should fill `.ai/project_context.md`, key `docs/`, `HANDOFF`, and `tasks/status.md` from the repo — **without changing application code** in that pass.

5. Skim the updated files; fix anything wrong.
6. Then normal workflow: **planner** → **POS MASTER PROMPT** → `Execute this.`

You can skip the bootstrap prompt if you prefer to edit `project_context.md` by hand.

## Layout

Adoption uses **integrated** layout: POS folders sit next to your existing `src/` at the repo root. That matches most existing repos.

**Sidecar** (`paws022/` + `main/`) is for **new** workspaces via `pos-new`; moving an old repo into sidecar means relocating code — not recommended unless you want that structure.

## Setup (`Setup-POS.bat` / pos-setup)

Choose **“Add POS to existing project”** during setup. After saving config, run `pos-adopt.ps1` on your project path.

## Updates later

```powershell
.\scripts\pos-sync.ps1 -TargetPath "C:\path\to\your-existing-project"
```

Syncs executor rules only; still does not touch `src/` or `project_context.md`.
