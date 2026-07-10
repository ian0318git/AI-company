# API Performance Profiling — Phase 2 Report

**Date:** 2026-07-10
**Pipeline:** web-fullstack (`6fb57396`)
**Idea:** API Performance Profiling & Optimization (`522fdfee`)

## N+1 Query Patterns (5 Confirmed)

| # | File | Lines | Pattern | Severity |
|---|------|-------|---------|----------|
| 1 | `api/routes/prompts.py` | 559-563 | Per-row template name lookup after GROUP BY | Medium |
| 2 | `api/routes/prompts.py` | 348-349, 630-688 | Per-experiment aggregate queries in A/B test listing | High |
| 3 | `api/routes/evolution.py` | 340-362 | Per-record AntibodyCandidate existence checks | Medium |
| 4 | `evolution/task_monitor.py` | 159-165 | Per-candidate FailureRecord check in monitor | Medium |
| 5 | `api/routes/tasks.py` | 68-75 | Per-slow-task FailureRecord lookup in evolution trigger | Low |

### Fix Strategy for Each

1. **Template name lookup**: Add JOIN in the original aggregate query or batch with `.in_()`
2. **A/B test listing**: Single `GROUP BY a_b_test_id, arm` query → hydrate in-memory
3. **AntibodyCandidate checks**: Batch query `AntibodyCandidate.failure_record_id.in_(ids)` → check in Python set
4. **Task monitor**: Batch query all `FailureRecord.task_id.in_(task_ids)` → check in Python set
5. **Evolution trigger**: Structure background loop to batch collect before querying

## Bulk-Scan Performance Concerns

| File | Pattern | Severity |
|------|---------|----------|
| `api/routes/dashboard.py` | Loads ALL rows from 5 tables | **High** |
| `api/routes/ws.py` | Loads ALL rows every 5s over WebSocket | **High** |
| `api/routes/tasks.py` | Loads ALL tasks for metrics | Medium |
| `api/routes/evolution.py` | Loads ALL ideas/tasks/pipelines | Medium |

**Fix:** Replace Python-level aggregation with SQL `GROUP BY` + `func.count()` / `func.sum()`.

## Missing Indexes

| Table | Column | Impact |
|-------|--------|--------|
| `tasks` | `project_id` | **High** |
| `tasks` | `status` | Medium |
| `pipelines` | `project_id` | **High** |
| `pipelines` | `idea_id` | Medium |
| `ideas` | `project_id` | Medium |
| `failure_records` | `task_id` | Medium |
| `failure_records` | `agent_role` | Medium |
| `failure_records` | `category` | Medium |
| `antibody_candidates` | `failure_record_id` | Medium |
| `event_logs` | `event_type` | Medium |
| `prompt_results` | `a_b_test_id` | Medium |

**Note:** SQLite does not auto-index FK columns despite FK constraints. Each needs explicit `index=True`.

## Existing Optimizations: **NONE**

Zero uses of `joinedload`, `selectinload`, or any eager loading strategy in the entire codebase.

## Next Steps (Phases 3-5)

- **Phase 3**: Measure endpoints under moderate concurrent load
- **Phase 4**: Generate optimization targets with measurable improvement goals
- **Phase 5**: Prioritize fixes by impact and begin implementation
