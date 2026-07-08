# Autonomous Cycle Health Dashboard — API & Data Model Spec

## Database Schema (SQLite extension)

```sql
-- Cycle run history
CREATE TABLE cycle_runs (
    id TEXT PRIMARY KEY,
    cycle_number INTEGER NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    ideas_processed INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running' -- running | completed | failed
);

-- Per-cycle token breakdown
CREATE TABLE cycle_token_usage (
    id TEXT PRIMARY KEY,
    cycle_id TEXT REFERENCES cycle_runs(id),
    agent_role TEXT NOT NULL,
    model_name TEXT,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER GENERATED ALWAYS AS (prompt_tokens + completion_tokens) STORED,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pipeline phase timing
CREATE TABLE pipeline_phase_timing (
    id TEXT PRIMARY KEY,
    pipeline_id TEXT REFERENCES pipelines(id),
    phase_name TEXT NOT NULL,
    entered_at TIMESTAMP NOT NULL,
    exited_at TIMESTAMP,
    duration_seconds INTEGER GENERATED ALWAYS AS (
        CAST((julianday(exited_at) - julianday(entered_at)) * 86400 AS INTEGER)
    ) STORED
);
```

## REST API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/cycles/` | List all autonomous cycles with summary metrics |
| `GET` | `/api/cycles/{id}` | Detail for one cycle (tasks, tokens, duration) |
| `GET` | `/api/cycles/metrics` | Aggregate metrics: avg time/task, token/cycle, throughput |
| `GET` | `/api/cycles/{id}/timeline` | Ordered event stream for the timeline visualization |
| `GET` | `/api/pipelines/{id}/phases` | Phase timing breakdown for pipeline Gantt |

## Data Sources (existing endpoints)
- `/api/tasks/metrics` — per-cycle task throughput
- `/api/evolution/status` — evolution system health
- `/api/pipelines/` — pipeline phase progression

## React Component Tree

```
DashboardLayout
├── CycleSummaryCard        — Latest cycle snapshot (ideas, tasks, tokens, time)
├── ThroughputFunnel        — Created → Refined → Pipeline → Done bar chart
├── TokenConsumptionChart   — Area chart: tokens per cycle over time
├── PipelineGantt           — Phase duration per pipeline (horizontal bars)
├── TaskCompletionRate      — Donut: done vs pending per cycle
├── EvolutionHealthCard     — Antibodies, vaccines, findings count
└── AutoRefreshToggle       — 15s/30s/60s interval picker
```
