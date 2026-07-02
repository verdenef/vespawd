# AI Providers

**Version:** 0.5.0

**Status:** Active — v0.5 freeze + M13 worker binding

## Purpose

Vedaws requests **AI capabilities**, not specific vendors. Provider plugins implement a neutral `AIProvider` interface. The runtime routes capability requests through configuration — no Gemini, OpenAI, Claude, or Cursor imports in the core.

---

## Capability Model

Workers and services request capabilities by name:

| Capability | Typical use |
|------------|-------------|
| `chat` | Conversational interaction |
| `plan` | Structured planning |
| `implement` | Code / asset generation |
| `review` | Review and critique |
| `summarize` | Condense information |
| `document` | Documentation generation |
| `refactor` | Refactoring assistance |
| `explain` | Explanation and teaching |

Constants live in `vedaws.ai.capabilities`. Workflows never embed provider names.

---

## Provider Interface

Plugins implement `AIProvider`:

| Method | Required | Description |
|--------|----------|-------------|
| `health()` | yes | Provider and credential availability |
| `chat(request)` | yes | Multi-turn completion |
| `generate(request)` | yes | Single-shot generation |
| `stream(request)` | stub ok | Token streaming |
| `embeddings(request)` | stub ok | Vector embeddings (future) |

Properties: `id`, `name`, `capabilities`, `priority`.

Public SDK exports: `vedaws.ai.sdk`.

---

## Provider Registry

Runtime-owned `AIProviderRegistry`:

- `register` / `unregister`
- `set_default` / `default_provider_id`
- `list_providers`
- `list_capabilities` — capability → provider ids (priority ordered)

Plugins contribute via `context.contribute_ai_provider(provider)`.

---

## Capability Routing

```
Project config [ai]
        ↓
Capability requested (e.g. implement)
        ↓
Preferred provider (per capability)
        ↓
Fallback chain
        ↓
Default provider
        ↓
Highest-priority registered provider
```

Configuration in `.vedaws/config.toml`:

```toml
[ai]
default_provider = "mock-ai"

[ai.capabilities.implement]
preferred = "mock-ai"
fallback = ["mock-ai"]
```

`AIService` is the runtime facade on `RuntimeContext`. Callers use `service.chat(...)` / `service.generate(...)` — not provider classes directly.

**M13 update:** workflow AI workers now call `AIService` during `execute()` via `AIExecutableWorker`. Routing remains available to CLI, doctor, and runtime code paths.

---

## CLI

| Command | Description |
|---------|-------------|
| `vedaws ai providers` | List registered providers |
| `vedaws ai capabilities` | Capability map and routing |
| `vedaws ai status` | Health and validation summary |

---

## Diagnostics

`vedaws doctor` **ai platform** check validates:

- Providers registered
- Capability bindings
- Credential availability (not values)
- Fallback chain integrity

---

## Reference Provider

`plugins/mock-ai/` — Mock AI Provider validating the SDK without external APIs.

---

## v0.5 freeze boundary

| Surface | Status at v0.5 |
|---------|----------------|
| `AIProvider` interface + `contribute_ai_provider` | **Frozen** |
| `AIService` on `RuntimeContext` | **Frozen** |
| `[ai]` capability routing config | **Frozen** |
| `STANDARD_AI_CAPABILITIES` | **Frozen** |
| `stream()` / `embeddings()` | Optional stubs; not production-ready platform-wide |
| Worker `execute()` → `AIService` | **Implemented** (M13 via `AIExecutableWorker`) |
| Credential vault | **Not implemented** (post-M14 backlog) |
| Vendor plugins (Gemini, OpenAI, …) | **Not in repo** — plugin-local packages only |

Frozen routing invariant: **no vendor SDK imports in `runtime/vedaws/`**. See [`ARCHITECTURE_FREEZE_V0.5.md`](../docs/ARCHITECTURE_FREEZE_V0.5.md).

---

## Relationship to Other Documents

| Document | Relationship |
|----------|--------------|
| `004_WORKERS.md` | Target: AI workers request capabilities via `AIService` (M13) |
| `010_PLUGINS.md` | `contribute_ai_provider` SDK |
| `012_CONFIGURATION.md` | `[ai]` configuration section |
| `005_AUTOMATION.md` | No `invoke_ai` action at v0.5; automation does not call `AIService` |
| `003_RUNTIME.md` | Bootstrap wires `AIService` before `AutomationEngine` |

---

## Non-goals (v0.5)

- Vendor plugins in core (Gemini, OpenAI, Claude, Cursor, MCP in `runtime/vedaws/`)
- Prompt engineering frameworks, agent orchestration, streaming UI in core
- Vendor-specific worker execution paths in core runtime (must remain plugin-owned)

---

## Future

- Real provider plugins (Gemini, etc.) as **separate plugin packages**
- Expand AI worker coverage across software/unity placeholder workflows
- Credential vault integration (post-M14 backlog)
- Production `stream()` and `embeddings()` implementations
- Automation actions invoking AI capabilities (after worker binding)
