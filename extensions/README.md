# pi_subagent extension

Load with:

```bash
cd /path/to/piPy
uv run pipy --extension /path/to/piPy-subagent/extensions/subagent_extension.py
```

Ensure `pi-subagent` is installed (via uv sync in the piPy-subagent repo).

Use `uv run pipy` (or `uv run pi` from the piPy repo) — not the global TypeScript `pi` CLI.

## OMA harness integration

oma-platform resolves the extension path via:

| Variable | Default |
|----------|---------|
| `PIPY_SUBAGENT_EXTENSION` | `../piPy-subagent/extensions/subagent_extension.py` (sibling of oma-platform) |

The host must configure `SubAgentRuntime` before the extension loads (see `oma_adapter/subagent_bridge.py`).

## Tests

```bash
cd /path/to/piPy-subagent
uv sync
uv run pytest packages/pi_subagent/tests/ -v
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OMA_DATABASE_PATH` | `./data/oma.db` | Agent config DB for `resolve_sub_agents()` |
| `DATABASE_PATH` | (fallback) | Alternate DB path env name |
| `PIPY_SUBAGENT_EXTENSION` | sibling repo path | Override extension file location |
