# API Performance Profiling & Optimization Report

**Generated**: 2026-07-11
**Idea**: API Performance Profiling & Optimization
**Phase**: 2 (ORM Query Profiling)

---

## Phase 1: Timing Middleware (Already Installed)
Timing middleware is deployed that captures per-endpoint latency and flags endpoints with p99 >500ms.

---

## Phase 2: SQLAlchemy ORM Query Profiling Results

### Current Database Stats
| Table | Rows |
|-------|------|
| ideas | 68 |
| pipelines | 93 |
| tasks | 565 |
| projects | 74 |
| teams | 94 |

### Missing Foreign Key Indexes (7 total)
All FK column joins cause **full table scans** — no indexes exist on any foreign key.

| Table | FK Column | References | Impact |
|-------|-----------|------------|--------|
| ideas | project_id | projects(id) | Joining ideas to projects scans all ideas |
| pipelines | project_id | projects(id) | Joining pipelines to projects scans all pipelines |
| pipelines | idea_id | ideas(id) | Joining pipelines to ideas scans all pipelines |
| tasks | project_id | projects(id) | Joining tasks to projects scans all tasks |
| tasks | parent_task_id | tasks(id) | Self-join on parent tasks scans all tasks |
| tasks | prompt_template_id | prompt_templates(id) | If table exists |
| teams | project_id | projects(id) | Joining teams to projects scans all teams |

**Recommendation**: Add indexes on all FK columns:
```sql
CREATE INDEX ix_ideas_project_id ON ideas(project_id);
CREATE INDEX ix_pipelines_project_id ON pipelines(project_id);
CREATE INDEX ix_pipelines_idea_id ON pipelines(idea_id);
CREATE INDEX ix_tasks_project_id ON tasks(project_id);
CREATE INDEX ix_tasks_parent_task_id ON tasks(parent_task_id);
CREATE INDEX ix_teams_project_id ON teams(project_id);
```

### N+1 Query Patterns Detected

**High Risk — Dashboard routes** (`dashboard.py`):
- Iterates pipelines list, each iteration hits related ideas/projects
- Iterates ideas list, computing per-idea status
- Iterates tasks list with per-item attribute access

**Medium Risk — Evolution routes** (`evolution.py`):
- Iterates ideas computing pipeline-type success rates
- Iterates done_tasks for slow-task detection per task

**Low Risk — Task routes** (`tasks.py`):
- Iterates in_progress tasks checking per-task status

### Existing Indexes
- All primary keys have auto-indexes
- 4 indexes on prompt_templates/prompt_results (specialized tables)

### Response Times (zero-load baseline)
| Endpoint | Latency | Notes |
|----------|---------|-------|
| GET /api/tasks/ | ~14ms | Fast at current row count |
| GET /api/ideas/ | ~13ms | Fast at current row count |
| GET /api/ideas/{id}/workflow | Error | 500 Internal Server Error |

---

## Recommendations (Priority Order)

| Priority | Action | Expected Impact |
|----------|--------|-----------------|
| P0 | Add 7 FK indexes | Eliminate full table scans on all joins |
| P1 | Fix N+1 in dashboard.py | Reduce dashboard load from O(n^2) to O(1) |
| P2 | Fix N+1 in evolution.py | Reduce evolution metrics computation |
| P3 | Fix /workflow endpoint 500 error | Restore workflow visualization |
| P4 | Add eager loading for common relationships | Prevent future N+1 regressions |

---

## Prioritized Fixes (Phase 5 Target)

1. **FK indexes** — 1 hour: add Alembic migration with 7 FK indexes
2. **Dashboard N+1** — 2 hours: refactor dashboard to use joined queries
3. **Evolution N+1** — 1 hour: batch-load instead of per-item
4. **Workflow 500** — 30 min: debug the internal server error
