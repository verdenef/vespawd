# Sprint 2 Summary — Worker Registry

**Status:** Complete  
**Version:** 0.1.0

Sprint 2 adds the worker layer on top of the Sprint 1 runtime skeleton. Workers are modeled, discovered, and managed — but do not execute tasks.

---

## 1. Repository Tree

```
vedaws/
├── pyproject.toml
├── VEDAWS_BOOTSTRAP.md
├── .gitignore
│
├── design/                         # Architecture documents (000–016)
│
├── runtime/vedaws/                 # Python package (install root)
│   ├── __init__.py                 # __version__ = "0.1.0"
│   ├── __main__.py
│   │
│   ├── cli/                        # CLI entry point
│   │   ├── app.py                  # vedaws command
│   │   └── commands.py             # init, doctor, status, version, workers
│   │
│   ├── config/                     # Layered configuration
│   │   ├── defaults.py
│   │   ├── loader.py
│   │   ├── paths.py
│   │   └── schema.py               # + WorkersConfig
│   │
│   ├── doctor/                     # Health checks
│   │   ├── checks.py               # + worker registry checks
│   │   └── model.py
│   │
│   ├── logging/
│   ├── plugins/                    # Plugin discovery (Sprint 1)
│   ├── project/                    # Project init/detection (Sprint 1)
│   │
│   ├── runtime/                    # Runtime bootstrap
│   │   ├── bootstrap.py            # + worker discovery
│   │   ├── context.py              # + worker_registry
│   │   └── status.py
│   │
│   ├── status/                     # Status reporting
│   │
│   └── workers/                    # Sprint 2 — Worker model
│       ├── interface.py            # Worker ABC
│       ├── models.py               # Metadata, capabilities, health
│       ├── types.py                # WorkerType enum
│       ├── status.py               # WorkerStatus, WorkerHealth
│       ├── manifest.py             # vedaws.worker.toml parser
│       ├── manifest_worker.py      # Manifest-backed implementation
│       ├── discovery.py            # Auto-discovery
│       ├── registry.py             # WorkerRegistry
│       └── reporter.py             # CLI formatting
│
├── workers/                        # Bundled worker manifests (data, not code)
│   ├── human/default/
│   ├── ai/{claude,gemini,chatgpt}/
│   └── tool/{git,docker,playwright,unity}/
│
├── plugins/hello/                  # Bundled plugin manifest (Sprint 1)
├── tests/                          # 18 tests (5 worker-specific)
│   ├── test_bootstrap.py
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_plugins.py
│   └── test_workers.py
│
├── examples/sprint1-demo/.vedaws/
└── {automation,docs,scripts,skills,templates}/   # Reserved scaffolds
```

---

## 2. Architecture Summary

```
CLI (vedaws workers | doctor | status)
         │
         ▼
Runtime Bootstrap
    ├── load_config()           defaults → user → project → env
    ├── discover_plugins()      → PluginRegistry
    ├── discover_workers()      → WorkerDiscoveryResult
    │       ├── workers[]
    │       ├── invalid[]
    │       └── duplicates[]
    └── RuntimeContext
            ├── registry            (plugins)
            ├── worker_registry       (workers)
            ├── project
            └── status: active
```

### Key Design Decisions

| Principle | Implementation |
|-----------|----------------|
| Provider-agnostic | `Worker` ABC + manifest metadata; no hardcoded AI/tool providers |
| Uniform model | `human`, `ai`, `tool` are types, not separate orchestration paths |
| Capability-based lookup | Registry matches by `work_type` + optional `scope`, not worker identity |
| Discovery over registration | Workers found via `vedaws.worker.toml` in search paths at bootstrap |
| Separation from runtime | Worker package is independent; runtime owns registry, not worker internals |
| Plugin-ready | Same manifest pattern as plugins; future plugin-registered workers slot in cleanly |

Configuration gained a `[workers]` section with `enabled` and `search_paths`, plus `VEDAWS_WORKERS_ENABLED` and `VEDAWS_WORKER_PATHS` environment overrides.

---

## 3. Public APIs and Interfaces Introduced

### CLI

| Command | Purpose |
|---------|---------|
| `vedaws workers [path]` | List registered workers (id, type, version, status, capabilities) |

`vedaws doctor` and `vedaws status` were extended but not renamed.

### Worker Interface (`vedaws.workers.interface.Worker`)

Abstract base class all future workers must implement:

| Member | Description |
|--------|-------------|
| `metadata` → `WorkerMetadata` | id, name, description, version, type, capabilities, status, provider |
| `health_check()` → `WorkerHealthReport` | Health without executing work |
| `id`, `status` | Convenience accessors |
| `set_status(status)` | Lifecycle management |

Sprint 2 implementation: `ManifestWorker` — metadata-only, no execution.

### Data Models (`vedaws.workers.models`)

| Type | Purpose |
|------|---------|
| `WorkerCapability` | work_type, scope, constraints, risk, available |
| `WorkerMetadata` | Full worker descriptor (frozen) |
| `WorkerHealthReport` | worker_id, health, message |
| `InvalidWorkerRecord` | path + reason for bad manifests |
| `DuplicateWorkerRecord` | worker_id, kept_path, skipped_path |

### Enums

| Enum | Values |
|------|--------|
| `WorkerType` | `human`, `ai`, `tool` |
| `WorkerStatus` | `registered`, `available`, `unavailable`, `invalid`, `retired` |
| `WorkerHealth` | `healthy`, `degraded`, `unhealthy`, `unknown` |

### Discovery (`vedaws.workers.discovery`)

| API | Returns |
|-----|---------|
| `discover_workers(config)` | `WorkerDiscoveryResult` |
| `parse_worker_manifest(path)` | `(WorkerMetadata \| None, error \| None)` |

`WORKER_MANIFEST_FILE` = `"vedaws.worker.toml"`

### Registry (`vedaws.workers.registry.WorkerRegistry`)

| Method | Purpose |
|--------|---------|
| `from_discovery(result)` | Build registry from discovery |
| `register(worker)` / `unregister(id)` | Add/remove workers |
| `get(id)` | Lookup by id |
| `list_workers()` | All workers, sorted by id |
| `list_by_type(type)` | Filter by `WorkerType` |
| `find_by_capability(work_type, scope?)` | Capability-based lookup |
| `health_reports()` | Health for all workers |
| `mark_available(id)` / `mark_unavailable(id)` | Lifecycle transitions |
| `.count`, `.invalid_count`, `.duplicate_count` | Summary properties |

### Runtime Integration

`RuntimeContext` gained:

- `worker_registry: WorkerRegistry`
- `worker_count: int` property

`bootstrap()` now calls `discover_workers()` and populates the registry automatically.

### Configuration (`vedaws.config.schema`)

| Type | Fields |
|------|--------|
| `WorkersConfig` | `enabled`, `search_paths` |

`VedawsConfig.workers` added; merged through the same layered loader as plugins.

### Manifest Contract (`vedaws.worker.toml`)

```toml
[worker]
id = "ai.claude"
name = "Claude"
description = "..."
version = "0.1.0"
type = "ai"            # human | ai | tool
provider = "anthropic" # optional, not interpreted by core

[[capabilities]]
work_type = "code-generation"
scope = "general"
risk = "medium"
constraints = ""
available = true
```

---

## 4. Directory Structure Overview

| Directory | Role |
|-----------|------|
| `runtime/vedaws/` | Executable Python package — all runtime code |
| `runtime/vedaws/workers/` | Worker abstraction, discovery, registry (Sprint 2 core) |
| `runtime/vedaws/runtime/` | Bootstrap and `RuntimeContext` — owns registries |
| `runtime/vedaws/config/` | Configuration loading and path resolution |
| `runtime/vedaws/cli/` | User-facing commands |
| `runtime/vedaws/doctor/` | Health checks including worker validation |
| `workers/` | **Data**: bundled worker manifest files (8 placeholders) |
| `plugins/` | **Data**: bundled plugin manifests |
| `tests/` | pytest suite (18 tests) |
| `design/` | Authoritative architecture specs |
| `examples/` | Demo projects (`.vedaws/` project dirs) |
| `{automation,skills,templates,scripts,docs}/` | Reserved for future sprints |

### Search Path Resolution

Workers and plugins follow the same pattern:

1. User dir — `~/.vedaws/workers/`
2. Install root — `vedaws/workers/`
3. Project dir — `.vedaws/workers/`
4. Environment — `VEDAWS_WORKER_PATHS`

---

## Current State

| Layer | Status |
|-------|--------|
| CLI | `init`, `doctor`, `status`, `version`, `workers` |
| Runtime bootstrap | Config, logging, plugins, workers, project detection |
| Plugin registry | Discovery + registration |
| Worker registry | Discovery + registration + capability lookup |
| Task execution | Not implemented (by design) |
| State machine | Not implemented (placeholder `state = "created"`) |

**18 tests passing.** Bundled workers: 8 (1 human, 3 AI, 4 tool).

---

## Suggested Next Sprint

**Sprint 3: Project State Machine**

1. Implement canonical state transitions per `design/006_STATE_MACHINE.md`
2. Persist transition history in `.vedaws/`
3. Add project state CLI commands
4. Wire `vedaws status` to real state semantics
5. Gate orchestration actions based on project state
