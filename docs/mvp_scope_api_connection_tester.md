# MVP Scope: API Connection Test Tool

> A minimal CLI utility that verifies the Autonomous API server (http://127.0.0.1:8765) is running and responsive.

## 1. What the Tool Does

The tool probes a running `ai-embedded-company` API server and reports three things:

| Check | What it tests | Endpoint(s) |
|---|---|---|
| **Health** | Server is alive, returns 200, body contains `"status":"healthy"` | `GET /health` |
| **Endpoints** | Core REST routes are registered and reachable | `GET /api/projects`, `/api/tasks`, `/api/ideas`, `/api/teams`, `/api/pipelines`, `/api/evolution` |
| **Timing** | Per-endpoint response time in ms + summary (fastest, slowest, average) | Same probes as above |

### Non-goals (out of scope for MVP)

- Pushing any data, creating/modifying resources
- Stress / load testing
- Authentication testing (API has none)
- Persistent output files or dashboards
- Anything beyond the CLI one-shot run
- Integration as a `aiteam` subcommand

## 2. CLI Usage Examples

```bash
# Quick health check (exit 0 if healthy, exit 1 otherwise)
uv run python -m ai_embedded_company.cli.check_api

# Full probe — health + all endpoints + timing report
uv run python -m ai_embedded_company.cli.check_api --verbose

# Probe a different host/port
uv run python -m ai_embedded_company.cli.check_api --host 192.168.1.100 --port 8765

# Custom timeout (default 5s per endpoint)
uv run python -m ai_embedded_company.cli.check_api --timeout 10
```

### Expected output (verbose mode)

```
API Connection Report — http://127.0.0.1:8765
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Health          OK   (0.023s)
 /api/projects   OK   (0.045s)
 /api/tasks      OK   (0.032s)
 /api/ideas      OK   (0.041s)
 /api/teams      OK   (0.028s)
 /api/pipelines  OK   (0.035s)
 /api/evolution  OK   (0.039s)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Fastest    0.023s  (Health)
 Slowest    0.045s  (/api/projects)
 Average    0.035s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Status: ALL 7 endpoints OK
```

### Output when failures occur

```
FAIL: /api/evolution returned 404
FAIL: /api/ideas timed out after 5s
 3 of 7 endpoints failed
```

Exit code is `1` — never a bare traceback.

## 3. Key Code Modules

A single file: `src/ai_embedded_company/cli/check_api.py` (~130 lines).

### Structure

```
check_api.py
├── module-level constants (ENDPOINTS list, DEFAULT config)
├── class ApiProbe
│   ├── __init__(host, port, timeout)
│   ├── probe_all() -> list[ProbeResult]
│   ├── _probe_single(endpoint) -> ProbeResult
│   └── report(results) -> None (prints to stdout)
└── def main()  (entry point: parse args, run probe, print report)
```

### Zero external dependencies beyond stdlib

- `urllib.request` / `urllib.error` for HTTP calls
- `json` for response body parsing
- `time` for timing
- `argparse` for CLI flags
- `sys` for exit codes
- `dataclasses` for ProbeResult

No httpx, no requests, no typer, no rich — keeps the tool trivially runnable without `uv sync` and allows it to work even when the server or database is broken.

### Why not typer?

The existing CLI (`aiteam`) uses typer, but importing typer pulls in the whole `ai-embedded-company` package graph (FastAPI, SQLAlchemy, etc.). For a connection tester that must function *when the server is down*, stdlib-only is the safer choice.

### ProbeResult type

```python
from dataclasses import dataclass

@dataclass
class ProbeResult:
    name: str
    ok: bool
    elapsed: float
    status_code: int
    error: str | None = None
```

## 4. What "Done" Looks Like

- [ ] File `src/ai_embedded_company/cli/check_api.py` exists and is <130 lines
- [ ] `uv run python -m ai_embedded_company.cli.check_api` runs without error against a running server
- [ ] `uv run python -m ai_embedded_company.cli.check_api` exits 1 gracefully when server is down (no traceback)
- [ ] `uv run python -m ai_embedded_company.cli.check_api --verbose` prints per-endpoint timing
- [ ] All output uses the project's preferred line length and style (ruff-compatible)
- [ ] No new dependencies added to `pyproject.toml`

### Manual validation checklist

1. Start the server: `uv run aiteam serve`
2. In another terminal, run: `uv run python -m ai_embedded_company.cli.check_api --verbose`
3. Verify output matches the format above
4. Stop the server, re-run, confirm graceful failure + exit code 1
5. Run `uv run ruff check src/ai_embedded_company/cli/check_api.py` — no violations

## 5. Future Considerations (explicitly NOT in MVP)

- Colored terminal output (would add `rich` or `ansicolors` dep)
- Connection retry / backoff logic
- JSON output flag for CI consumption
- Continuous monitoring mode (`--watch`)
- Integration into `aiteam check` as a subcommand
