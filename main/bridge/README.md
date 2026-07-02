# Vespawd Bridge

Standalone sync layer between PAWS (`paws022/`) and Vedaws (`main/.vedaws/`). Tool-neutral — invoke via subprocess from any Executor.

## Requirements

- Python 3.11+
- Vedaws 0.5.0+ on PATH or path in `manifest.toml` `[vedaws].cli`

## Invoke (Executor)

```bash
python main/bridge/bin/bridge invoke bootstrap \
  --context context.json \
  --input '{}'
```

`context.json`:

```json
{
  "workspace_root": "/absolute/path/to/vespawd"
}
```

Operations: `bootstrap`, `ingest_master_prompt`, `sync_status`, `pre_implement_check`, `post_implement`, `post_phase_complete`, `pre_documenter`.

Output: `BridgeResult` JSON (`ok`, `codes`, `blockers`, `warnings`, `vedaws_task_id`, `project_state`, `files_touched`, `recovery`, `duration_ms`, `vedaws_commands_run`).

## Layout

- `manifest.toml` — paths, phase map, Vedaws CLI
- `lib/vespawd_bridge/` — implementation modules
- `bin/bridge` — CLI entry
- `tests/` — unit and integration suites

## Tests

```bash
cd main/bridge
pip install -e ".[dev]"
pytest
```
