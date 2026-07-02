# Project folder layout

POS (**paws022**) supports two layouts. Pick one in setup or when you run `pos-new`.

## Integrated (default)

One folder **is** your app. POS and code share the root.

```
{{PROJECTS_DIR}}/
  my-api/                    ← open THIS in your executor IDE
  ├── .ai/
  ├── docs/
  ├── tasks/
  ├── src/                   ← your application code
  └── .cursor/rules/
```

```powershell
pos-new my-api
```

**Best for:** one GitHub repo, simplest workflow.

---

## Sidecar (paws022 + app)

Workspace has **`paws022/`** (POS) beside **`main/`** (or `app/`) for your code.

```
{{PROJECTS_DIR}}/
  my-api/                    ← open THIS workspace root in your executor IDE
  ├── README.md
  ├── paws022/               ← POS (tasks, .ai, docs, HANDOFF)
  │   ├── .ai/
  │   ├── tasks/
  │   └── docs/
  └── main/                  ← application only (name configurable)
      ├── src/
      └── README.md
```

```powershell
pos-new my-api -Layout sidecar -AppFolderName main
```

Defaults in `%USERPROFILE%\.pos\config.json`:

```json
"projectLayout": "sidecar",
"posFolderName": "paws022",
"appFolderName": "main"
```

**Best for:** keeping POS files separate from “real” project code — matches `dev/proj1/paws022` + `dev/proj1/main`.

**Publishing note (default):** In sidecar layout, git is initialized in the **app folder** (e.g. `main/`) so `paws022/` is not published to GitHub by default.

---

## Template repo vs app workspace

| What | Where |
|------|--------|
| **GitHub template** `verdenef/paws022` | Clone once; run setup; maintain template |
| **Sidecar app** | `pos-new` copies template **into** `workspace/paws022/` |
| **Integrated app** | `pos-new` copies template **into** `workspace/` root |

See [START.md](../START.md).
