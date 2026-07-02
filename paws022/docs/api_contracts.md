# API Contracts (POS Memory)

> **Per-project.** Public interface catalog. Keep in sync with `src/` or delete sections that do not apply (e.g. CLI-only projects).

## Conventions

| Field | Value |
|-------|--------|
| Base URL | |
| Auth | |
| Content-Type | `application/json` (unless noted) |

### Standard Error Body

```json
{
  "error": "human-readable message",
  "code": "OPTIONAL_MACHINE_CODE",
  "details": {}
}
```

## Endpoint Template

Copy for each endpoint:

### `{METHOD} {path}`

**Description:** _

**Auth:** _

**Request**

```json
```

**Response `{status}`**

```json
```

**Errors**

| Status | When |
|--------|------|

---

## Endpoints

### `GET /health` _(example—remove when bootstrapped)_

**Response 200**

```json
{ "status": "ok" }
```
