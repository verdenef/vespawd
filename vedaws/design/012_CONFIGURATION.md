# Configuration

**Version:** 0.5.0

**Status:** Active — M16 baseline (plugin schema integration included)
## Purpose

This document describes how Vedaws loads configuration today. It specializes configuration concepts referenced in `003_RUNTIME.md`.

---

## Layering

Configuration is merged in order (later overrides earlier):

| Layer | Location | Scope |
|-------|----------|-------|
| Defaults | `runtime/vedaws/config/defaults.py` | Built-in |
| User | `~/.vedaws/config.toml` | All workspaces |
| Project | `<project>/.vedaws/config.toml` | Single project |
| Environment | `VEDAWS_*` variables | Process |

Implemented in `vedaws.config.loader.load_config()`.

---

## Schema (implemented)

### `[logging]`

| Key | Type | Default |
|-----|------|---------|
| `level` | string | `INFO` |
| `file` | string \| null | null |

Environment: `VEDAWS_LOG_LEVEL`, `VEDAWS_LOG_FILE`

### `[plugins]`

| Key | Type | Default |
|-----|------|---------|
| `enabled` | bool | true |
| `search_paths` | list[string] | Auto-discovered if empty |

Environment: `VEDAWS_PLUGINS_ENABLED`, `VEDAWS_PLUGIN_PATHS` (pathsep-separated)

### `[workers]`

| Key | Type | Default |
|-----|------|---------|
| `enabled` | bool | true |
| `search_paths` | list[string] | Auto-discovered if empty |

Environment: `VEDAWS_WORKERS_ENABLED`, `VEDAWS_WORKER_PATHS`

### `[runtime]`

| Key | Type | Default |
|-----|------|---------|
| `name` | string | `vedaws` |

Environment: `VEDAWS_RUNTIME_NAME`

### `[ai]` (Milestone 12)

| Key | Type | Description |
|-----|------|-------------|
| `default_provider` | string | Default AI provider id |
| `capabilities.<name>.preferred` | string | Preferred provider for capability |
| `capabilities.<name>.fallback` | list[string] | Fallback provider chain |

Example:

```toml
[ai]
default_provider = "mock-ai"

[ai.capabilities.chat]
preferred = "mock-ai"
fallback = ["mock-ai"]
```

See `017_AI_PROVIDERS.md`.

### `[security]` (Milestone 14)

| Key | Type | Description |
|-----|------|-------------|
| `allow_env_secrets` | bool | Whether plugins may rely on environment-based secret sources |
| `allow_file_secrets` | bool | Whether plugins may rely on file-based secret sources |

Example:

```toml
[security]
allow_env_secrets = true
allow_file_secrets = false
```

This section exposes secret-source availability only. Vedaws core still does not store credential values.

### Extensions

Unknown top-level TOML sections are preserved in `VedawsConfig.extensions` for forward compatibility.

---

## Project manifest (separate from config)

`project.toml` is loaded via `load_project_section()` — not merged into `VedawsConfig`:

```toml
[project]
name = "my-project"
state = "created"
```

---

## Path constants

Defined in `vedaws.config.paths`:

| Constant | Value |
|----------|-------|
| Project config dir | `.vedaws` |
| State file | `state.toml` |
| History file | `transitions.jsonl` |
| Workflows dir | `workflows` |
| Progress file | `workflow-progress.json` |
| Automation rules | `automation.toml` |
| Plugin activation | `plugins.toml` |

---

## Plugin activation (`plugins.toml`)

Separate from runtime config — controls which discovered plugins are active.

**Global:** `~/.vedaws/plugins.toml`  
**Per-project:** `.vedaws/plugins.toml` (created by `vedaws init`)

```toml
[plugins]
enabled = ["hello"]
disabled = []
```

| Key | Meaning |
|-----|---------|
| `enabled` | Explicit allow-list; empty means all except `disabled` |
| `disabled` | Deny-list merged from global + project |

Managed via `vedaws plugins enable|disable`.

---

## Plugin configuration integration (M16)

Plugins may call `contribute_configuration(schema)` during registration. Runtime bootstrap applies contributed schemas to the loaded `VedawsConfig`:

- schema defaults are merged into plugin-owned config sections
- plugin config values are validated against declared schema field types
- validated values remain available under `VedawsConfig.extensions`
- unknown top-level sections continue to be preserved for backward compatibility

`VedawsConfig.extensions` remains the forward-compatibility container for plugin and unknown sections, but schema-backed plugin sections are now validated and defaulted by the runtime.

---

## TODO

- Document configuration validation and schema versioning — deferred (review P2).
- Extend plugin configuration schema types and nested validation support.
- Secrets handling value storage/vault integration — post-M14 (`013_SECURITY.md`).
