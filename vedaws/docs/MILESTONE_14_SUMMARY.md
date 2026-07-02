# Milestone 14 Summary — Security & Trust Model

**Status:** Complete  
**Version:** 0.1.0  
**Type:** Security and trust hardening (additive, v0.5-compatible)

Milestone 14 implements the first security/trust layer for Vedaws without redesigning core orchestration: plugin security declarations, manifest validation hooks, doctor security diagnostics, and runtime security config for secrets source availability.

---

## 1. Repository Tree

```
vedaws/
├── design/
│   ├── README.md                      # 013 status promoted to Active
│   ├── 010_PLUGINS.md                # security declaration schema + diagnostics
│   ├── 012_CONFIGURATION.md          # [security] config section
│   ├── 013_SECURITY.md               # M14 baseline trust model
│   ├── 015_ROADMAP.md                # M14 completion status
│   └── 016_IMPLEMENTATION_PLAN.md    # M14 status update
│
├── docs/
│   ├── API_STABILITY.md              # additive frozen [security] surfaces
│   └── MILESTONE_14_SUMMARY.md
│
├── plugins/git/
│   └── vedaws.plugin.toml            # declared subprocess/file permissions
│
├── runtime/vedaws/
│   ├── config/
│   │   ├── schema.py                 # SecurityConfig
│   │   ├── defaults.py               # security defaults
│   │   └── loader.py                 # security parsing + env overrides
│   ├── plugins/
│   │   ├── manifest.py               # PluginSecurity model
│   │   ├── manifest_parser.py        # [security] parsing
│   │   ├── security.py               # security validation helpers
│   │   └── validation.py             # manifest security validation
│   └── doctor/checks.py              # plugin security health check
│
└── tests/
    ├── test_cli.py
    ├── test_config.py
    ├── test_plugins.py
    └── test_plugins_platform.py
```

---

## 2. Architecture Summary

```
Plugin manifest (vedaws.plugin.toml)
        ↓
Optional [security] declaration
        ↓
Manifest parser + validator (activation-time checks)
        ↓
Plugin platform lifecycle (fail invalid plugins early)
        ↓
Doctor plugin security check (runtime diagnostics)
        ↓
Runtime [security] config governs secret-source availability
```

M14 is additive and preserves all v0.5 frozen orchestration contracts.

---

## 3. Runtime Changes

| Area | Change |
|------|--------|
| Plugin manifest model | Added `PluginSecurity` with `permissions`, `subprocess_allow`, `network` |
| Manifest parsing | Added `[security]` parsing in manifest parser |
| Plugin validation | Added security declaration validation (unknown permissions, invalid combinations) |
| Doctor checks | Added `plugin security` health check to surface policy violations/warnings |
| Config schema | Added `SecurityConfig` to `VedawsConfig` |
| Config defaults | Defaulted `allow_env_secrets=true`, `allow_file_secrets=false` |
| Config loader | Added `[security]` TOML parsing and env overrides (`VEDAWS_ALLOW_ENV_SECRETS`, `VEDAWS_ALLOW_FILE_SECRETS`) |

Git plugin now declares explicit filesystem + subprocess permissions and subprocess allow-list (`git`).

---

## 4. Public API Changes

All changes are additive and backward-compatible.

| Surface | Change |
|---------|--------|
| `vedaws.plugin.toml` | New optional `[security]` section |
| `VedawsConfig` | New additive `security` section |
| Project/user config | New optional `[security]` keys (`allow_env_secrets`, `allow_file_secrets`) |

No breaking changes to worker contracts, dispatcher APIs, plugin SDK contribution methods, automation action types, or AI provider interfaces.

---

## 5. Design Decisions

1. **Declarative first:** permission metadata is declared in plugin manifests, not inferred dynamically.
2. **Validation before activation:** invalid security declarations fail in plugin validation, preventing activation drift.
3. **Diagnostics over sandboxing (M14 scope):** doctor surfaces trust-policy issues; OS-level sandboxing remains deferred.
4. **Backwards compatibility:** plugins without `[security]` remain valid to avoid breaking existing ecosystem behavior.
5. **No secrets in core config values:** runtime only models secret-source availability, not credential storage.

---

## 6. Test Coverage

| Test file | Coverage |
|-----------|----------|
| `tests/test_config.py` | Security defaults + `[security]` parsing + env override behavior |
| `tests/test_plugins.py` | Security declaration validation (unknown permission rejection) |
| `tests/test_plugins_platform.py` | Invalid security declaration blocks activation |
| `tests/test_cli.py` | Doctor output includes plugin security check |

Regression: all prior test areas (workflow/dispatch/plugins/automation/AI) still pass.

---

## 7. Deferred Work

- OS/process sandboxing and hard isolation between plugins
- Signed plugin bundles and provenance verification
- Enforced runtime permission mediation (current model is declaration + validation + diagnostics)
- Secret storage backends/vault integration (source availability only implemented)
- Policy tiers (strict/enterprise) and central enforcement profiles

---

## 8. Test Results

```bash
python -m pytest tests/ -q
# 115 passed in 8.89s
```
