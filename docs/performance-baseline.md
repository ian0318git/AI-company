# API Performance Baseline Report

**Date**: 2026-07-10
**Project**: AI Embedded Systems Company
**Method**: Single-request curl latency measurement (cold start)

---

## Endpoint Latency Baseline

| Endpoint | Latency | Status |
|---|---|---|
| `/health` | 0.96ms | 🟢 |
| `/api/projects/` | 2.1ms | 🟢 |
| `/api/ideas/` | 2.6ms | 🟢 |
| `/api/pipelines/` | 4.2ms | 🟢 |
| `/api/tasks/metrics` | 4.5ms | 🟢 |
| `/api/dashboard/metrics` | 8.1ms | 🟢 |
| `/api/tasks/` | 8.2ms | 🟢 |
| `/api/evolution/status` | 11.0ms | 🟢 |

**All endpoints are well under 500ms threshold.** No immediate performance issues detected.

---

## Database Schema Analysis

### Tables (15)
- Largest: tasks (153 rows), event_logs (57), teams (33), pipelines (30), projects (28), ideas (27), knowledge (25)

### Index Coverage

**Present indexes** (18 total):
- Primary keys: auto-indexed on all tables
- `ix_prompt_results_a_b_test_id`, `ix_prompt_results_task_id`, `ix_prompt_results_template_id`
- `ix_prompt_templates_agent_role`

**Missing indexes (optimization targets):**

| Table | Column(s) | Impact |
|---|---|---|
| `tasks` | `project_id` | Frequent filter by project — N+1 risk without index |
| `tasks` | `status` | Filter by status (pending/done) — used in dashboard |
| `ideas` | `status` | Filter by status (new/refining/done) |
| `pipelines` | `project_id` | Join/project lookup |
| `pipelines` | `current_phase` | Phase-based filtering |
| `event_logs` | `event_type, created_at` | Time-series queries without index |
| `failure_records` | `severity, status` | Categorization queries |

---

## Recommendations

### Tier 1 — Quick Wins (Low Effort, High Impact)
1. Add index on `tasks(project_id)` — most-frequent join column
2. Add index on `tasks(status)` — dashboard queries filter by status
3. Add composite index on `pipelines(project_id, current_phase)`

### Tier 2 — Baseline Monitoring
4. Set up periodic latency capture (every 100 cycles)
5. Add endpoint timing middleware to log p50/p95/p99

### No Action Needed
- All endpoints pass the 500ms threshold
- Database is small (153 rows max) — indexes become critical at 10k+ rows
- No N+1 query patterns detected in basic profiling
