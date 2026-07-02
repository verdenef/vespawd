# Milestone 7 Summary — Git Plugin (First-Party Plugin)

**Status:** Complete  
**Version:** 0.1.0  
**Type:** First production plugin validating the Plugin Platform

Milestone 7 implements the Git plugin entirely through the public Plugin SDK. The runtime gains generic plugin command dispatch but no Git-specific logic.

---

## 1. Repository Tree

```
vedaws/
├── design/
│   └── 010_PLUGINS.md              # v0.3.0 — command dispatch + Git reference
│
├── docs/
│   └── MILESTONE_7_SUMMARY.md
│
├── plugins/
│   └── git/                        # First-party Git plugin
│       ├── vedaws.plugin.toml
│       └── git_plugin/
│           ├── __init__.py         # GitPlugin
│           ├── commands.py         # CLI handlers
│           ├── errors.py           # Typed Git errors
│           ├── repository.py       # git CLI wrapper
│           └── workers.py          # Dispatchable Git workers
│
├── runtime/vedaws/
│   ├── cli/
│   │   ├── app.py                  # Plugin parser registration at build time
│   │   └── plugin_commands.py      # Generic plugin CLI dispatch
│   ├── doctor/checks.py            # Workspace-aware plugin health checks
│   └── plugins/
│       ├── commands.py             # collect_plugin_command_groups()
│       ├── contributions.py        # PluginCommand.group
│       └── sdk.py                  # contribute_command(group=...)
│
└── tests/
    └── test_git_plugin.py          # Git plugin + CLI + worker tests
```

---

## 2. Architecture Summary

```
vedaws git status
  ↓
CLI (plugin_commands.py) — generic dispatch, no Git imports
  ↓
GitPlugin.commands.cmd_status — plugin handler
  ↓
GitRepository — subprocess git CLI
```

```
Workflow task (capability: git-status)
  ↓
WorkerDispatcher
  ↓
git.status worker (GitStatusWorker)
  ↓
GitRepository
```

**Separation:** Runtime knows about `PluginCommand` groups and handlers. All Git domain logic is in `plugins/git/`.

---

## 3. Public APIs

### Platform (extended in M7)

| API | Purpose |
|-----|---------|
| `PluginCommand.group` | Top-level CLI group name (`git`) |
| `PluginContext.contribute_command(..., group=...)` | Register grouped subcommands |
| `collect_plugin_command_groups()` | Bootstrap + collect active command handlers |
| `register_plugin_command_parsers()` | Dynamic argparse registration |

### Git plugin (plugin-local, not runtime)

| Module | Purpose |
|--------|---------|
| `GitRepository` | Repository detection, status, branch, stage, commit, fetch, pull, push |
| `GitError` hierarchy | Typed errors for CLI and workers |
| `all_git_workers()` | Six executable workers for dispatch |
| `commands.cmd_*` | CLI handlers for `vedaws git *` |

---

## 4. Plugin Lifecycle

The Git plugin follows the standard platform lifecycle (unchanged from M6):

```
DISCOVER (plugins/git/vedaws.plugin.toml)
  → VALIDATE (manifest v1 + compatibility)
  → LOAD (git_plugin:GitPlugin)
  → INITIALIZE (on_load)
  → ACTIVE (register workers, commands, health checks)
```

Activation: enabled by default in new projects via `.vedaws/plugins.toml` (`hello`, `git`).

---

## 5. Git Plugin Architecture

```
GitPlugin.register()
  ├── Workers (6)
  │     git.status, git.branch, git.commit, git.fetch, git.pull, git.push
  ├── Commands (6) — group "git"
  │     status, branch, commit, fetch, pull, push
  ├── Health checks (4)
  │     installation, plugin, workers, repository
  └── Configuration schema
        git.default_remote
```

**Repository layer** (`repository.py`):

- Uses `git` executable via subprocess (no GitPython)
- `GitRepository.open(path)` validates repository
- Porcelain status parsing, branch detection, detached HEAD detection
- Push auth failures → `GitAuthError` (stub/warn, exit 0 for CLI push)

---

## 6. Example Usage

```bash
# Initialize project (enables hello + git plugins)
vedaws init .

# Inside a git repository
vedaws git status
vedaws git branch
vedaws git branch --create feature/my-work
vedaws git commit -m "Initial commit" --stage-all
vedaws git fetch
vedaws git pull
vedaws git push          # warns if authentication unavailable

# Plugin management
vedaws plugins info git
vedaws doctor            # includes git installation, workers, repository checks

# Worker dispatch (workflow task capability: git-status)
vedaws workers run git.status
```

---

## Error Handling

| Condition | Error | CLI exit |
|-----------|-------|----------|
| Git not installed | `GitNotInstalledError` | 1 |
| Not a repository | `NotARepositoryError` | 1 |
| Detached HEAD (branch/commit) | `DetachedHeadError` | 1 |
| Merge conflicts on pull | `MergeConflictError` | 1 |
| Push without auth | `GitAuthError` | 0 (warning stub) |

---

## Tests

```bash
python -m pytest tests/ -q
# 65 passed (skipped if git not installed)
```

---

## Non-goals (confirmed)

No Git logic added to runtime core. No Cursor, Gemini, Unity, Docker, Playwright, Automation, Event Bus, or AI providers.
