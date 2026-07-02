# Bridge hooks (extension points)

Optional v1 stubs. Hooks MUST NOT modify the Vedaws CLI allowlist, write `.vedaws/` directly, or override `ok` without adding codes.

| Hook | When |
|------|------|
| `after_prepare` | After manifest load |
| `before_cli` | Before each CLI call |
| `after_projection` | After status write |
| `on_failure` | When `ok=false` |

Hook interface receives `BridgeContext`, `ResolvedPaths`, read-only `ManifestModel`.
