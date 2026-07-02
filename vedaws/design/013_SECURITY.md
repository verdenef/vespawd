# Security

**Version:** 0.5.0

**Status:** Active — M14 Security & Trust baseline

## Purpose

This document describes the **trust and security posture of Vedaws at architecture v0.5 freeze**. It records what is implemented today — not a target production security model.

Vedaws is a **local Development OS** that loads and executes plugin code with the privileges of the invoking user. Security hardening is explicitly deferred to post-freeze milestones.

---

## v0.5 trust model (implemented)

### Assumptions

| Assumption | Implication |
|------------|-------------|
| Plugins are **trusted** | Any activated plugin runs arbitrary Python in-process |
| Workspace is **user-controlled** | Vedaws reads and writes under the project root and `~/.vedaws/` |
| External tools are **invoked directly** | Plugins may call subprocesses (e.g. Git on PATH) |
| No multi-tenant isolation | Single user, single machine; no sandbox between plugins |

### What the runtime enforces today

| Control | Implementation |
|---------|----------------|
| Plugin activation gate | `plugins.toml` enable/disable (`012_CONFIGURATION.md`) |
| Manifest validation | `vedaws.plugin.toml` schema v1 (`010_PLUGINS.md`) |
| Dependency ordering | Semver-compatible dependency resolution before activation |
| Orchestration policy | Automation depth limit, state eligibility gates (`005_AUTOMATION.md`, `006_STATE_MACHINE.md`) |
| Health reporting | `vedaws doctor` and plugin `contribute_health_check` |

### M14 security extensions (additive)

M14 extends the trust model with **declarative permissions and validation hooks** while preserving all v0.5 frozen orchestration contracts.

| Extension | Layer | Purpose |
|-----------|-------|---------|
| Plugin permission declaration | `vedaws.plugin.toml` | Make trust assumptions explicit per plugin |
| Manifest permission validation | Plugin validation | Reject invalid permission declarations early |
| Doctor permission check | Runtime diagnostics | Report missing/unsafe permission policies |
| Secrets availability config | Runtime config | Expose whether environment/file-secret sources are permitted |

### What the runtime does **not** enforce

| Gap | Risk (per architecture review) |
|-----|--------------------------------|
| Plugin sandbox / isolation | Plugin crash or malicious code affects entire process |
| Permission enforcement | Declarations/doctor checks exist, but no OS-level enforcement layer |
| Subprocess policy | Git plugin runs `git` with user credentials and environment |
| Secrets / credential vault | AI providers report availability only; no secure storage in core |
| Signed or remote plugin distribution | Local discovery only; no trust chain |
| Config schema merge for plugin secrets | `contribute_configuration` registered but not merged |

---

## Known risks at freeze

From [`ARCHITECTURE_REVIEW_V0.5.md`](../docs/ARCHITECTURE_REVIEW_V0.5.md) §Biggest risks:

1. **Security vacuum** — `013_SECURITY.md` was empty at review; plugins run arbitrary code with subprocess access.
2. **String-based cross-plugin coupling** — automation invokes workers by id without declared trust boundaries.
3. **Ghost configuration API** — plugin config schemas registered but not applied; contributors may assume validation exists.

These are **documented limitations**, not oversights to fix silently during the freeze sprint.

---

## Frozen for v0.5

The following posture was frozen through M14 and remains the current baseline:

- **Trust-all local plugins** — activation is the primary security gate
- **No core sandbox** — domain logic remains in plugins; core does not wrap subprocesses globally
- **No secrets in project TOML** — `[ai]` routing uses provider ids only; credentials belong in future layers

Changing to a deny-by-default or sandboxed model requires architecture review and updates to [`API_STABILITY.md`](../docs/API_STABILITY.md).

M14 does **not** introduce a sandbox, process isolation, or remote attestation. Activation remains the primary trust gate.

---

## Plugin permission manifest (M14)

Plugins may declare security posture in `vedaws.plugin.toml`:

```toml
[security]
permissions = ["filesystem.read", "filesystem.write", "subprocess.exec"]
subprocess_allow = ["git"]
network = "none" # one of: none, outbound
```

### Permission identifiers

| Permission | Meaning |
|------------|---------|
| `filesystem.read` | Plugin reads files under workspace/user scope |
| `filesystem.write` | Plugin writes files under workspace/user scope |
| `subprocess.exec` | Plugin executes local subprocess commands |
| `network.outbound` | Plugin may access outbound network resources |

### Validation rules

1. Unknown permission names are invalid.
2. If `subprocess.exec` is declared, `subprocess_allow` should list expected command names.
3. `network` must be one of `none` or `outbound`.
4. Missing `[security]` is allowed for backward compatibility.

These are declarative constraints and diagnostics, not kernel-level enforcement.

---

## Plugin-local security patterns (implemented examples)

| Plugin | Pattern |
|--------|---------|
| `git` | Subprocess wrapper (`GitRepository`); errors typed as `GitError`, `GitAuthError`; assumes `git` on PATH |
| `mock-ai` | No external network; validates AI SDK path only |
| Domain plugins (`software`, `unity`) | Placeholder workers touch scaffold files only; no elevated privileges beyond filesystem |

Plugin authors are responsible for safe subprocess use within the trust model above.

---

## Configuration and secrets

| Layer | Secrets handling at v0.5 |
|-------|--------------------------|
| `~/.vedaws/config.toml` | User-local settings; no credential section in core schema |
| `.vedaws/config.toml` | Project settings including `[ai]` routing; no vault |
| Environment | `VEDAWS_*` for logging, paths, plugins, workers, runtime (`012_CONFIGURATION.md`) |
| Plugin `contribute_configuration()` | Merged/validated into `VedawsConfig.extensions` during bootstrap (M16) |

Future credential interfaces must not pollute committed project TOML without explicit design (`012_CONFIGURATION.md` TODO).

### M14 secrets availability interface

Runtime config adds an additive security section:

```toml
[security]
allow_env_secrets = true
allow_file_secrets = false
```

This interface controls **allowed secret sources** for plugins and diagnostics. It does not store secret values in Vedaws core.

---

## Relationship to other documents

| Document | Relationship |
|----------|--------------|
| `010_PLUGINS.md` | Plugin lifecycle, sandbox deferral, `contribute_configuration` limitation |
| `012_CONFIGURATION.md` | Config layering; secrets deferred |
| `017_AI_PROVIDERS.md` | Provider `health()` is boolean availability; no credential management |
| `015_ROADMAP.md` | M14 completed and post-freeze security backlog |
| [`docs/API_STABILITY.md`](../docs/API_STABILITY.md) | Unstable APIs including `extensions` dict and plugin config merge |

---

## Subprocess policy hooks (M14)

Vedaws remains plugin-local for subprocess execution. M14 adds policy hooks:

- Manifest-level declaration (`subprocess.exec`)
- Optional allow-list (`subprocess_allow`)
- Doctor check surfaces policy violations/missing declarations
- Git plugin serves as reference implementation with explicit subprocess declaration

No runtime global subprocess wrapper is introduced in M14.

---

## Relationship to freeze and API stability

M14 is additive and does not break v0.5 frozen contracts:

- Worker dispatch remains capability-based.
- Automation still dispatches workers only.
- AI providers remain plugin-owned.
- `TaskDispatch` / `TaskOutcome` contract unchanged.
- No vendor-specific runtime imports.

---

## TODO

- Add stronger policy tiers (dev/strict) after v0.5 if needed
- Consider plugin signature and provenance verification (post-v1)
- Coordinate with `009_MEMORY.md` if retention policies affect stored context
