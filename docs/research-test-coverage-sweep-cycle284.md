# Test Coverage Sweep — Cycle #284

**Date:** 2026-07-10
**Type:** research-spike (auto-seeded cycle #284)

## Coverage Summary

| Metric | Value |
|--------|-------|
| Overall coverage | **42%** (2459/4268 statements missed) |
| Source modules examined | 42 |
| Modules with complete coverage (skipped) | 15 |
| Total tests | 228 |
| Tests passing | 227 |
| Tests failing | 1 |
| Test time | ~116s |

## Module-by-Module Coverage

### High Coverage (≥60%)
| Module | Coverage |
|--------|----------|
| `tools/idle_detector.py` | 98% |
| `evolution/classifier.py` | 97% |
| `config.py` | 96% |
| `storage/database.py` | 93% |
| `api/app.py` | 97% |
| `api/routes/ws.py` | 88% |
| `api/routes/teams.py` | 75% |
| `api/routes/prompts.py` | 57% |
| `api/pagination.py` | 56% |
| `mcp/server.py` | 56% |
| `mcp/tools/system.py` | 57% |

### Medium Coverage (25-55%)
| Module | Coverage |
|--------|----------|
| `mcp/tools/project.py` | 52% |
| `mcp/tools/pipeline.py` | 48% |
| `mcp/tools/team.py` | 48% |
| `evolution/task_monitor.py` | 42% |
| `api/routes/pipelines.py` | 40% |
| `mcp/tools/meeting.py` | 41% |
| `mcp/_autostart.py` | 27% |
| `api/routes/ideas.py` | 27% |
| `mcp/tools/task.py` | 26% |
| `mcp/tools/knowledge.py` | 27% |

### Low Coverage (<25%) — Priority targets
| Module | Coverage | Priority |
|--------|----------|----------|
| `api/routes/tasks.py` | 30% | **HIGH** — core route |
| `api/routes/projects.py` | 32% | **HIGH** — core route |
| `api/routes/system.py` | 32% | **MEDIUM** |
| `api/routes/evolution.py` | 31% | **MEDIUM** |
| `api/routes/dashboard.py` | 29% | **MEDIUM** |
| `mcp/tools/evolution.py` | 15% | **MEDIUM** |
| `mcp/tools/code.py` | 21% | **LOW** |
| `mcp/tools/idea.py` | 17% | **LOW** |
| `mcp/tools/memory.py` | 19% | **LOW** |
| `mcp/tools/hardware.py` | 20% | **LOW** |
| `mcp/_base.py` | 21% | **LOW** |
| `mcp/tools/guardrails.py` | 24% | **LOW** |

### Zero Coverage — 11 modules
All CLI, hook, and orchestrator modules have **0% coverage**:
- `cli/app.py`, `cli/check_api.py`, `cli/health_check.py`
- `hooks/context_monitor.py`, `hooks/guardrails.py`, `hooks/inject_context.py`, `hooks/pre_compact_save.py`, `hooks/send_event.py`, `hooks/session_bootstrap.py`
- `orchestrator/__init__.py`, `orchestrator/state.py`
- `templates/m5stack/sensor_demo.py`
- `tools/connection_tester.py`

## Prioritized Fill Plan

### Round 1 — Core API routes (estimated 2-3 days)
Target modules: `routes/ideas.py`, `routes/tasks.py`, `routes/projects.py`
- These handle the main CRUD operations the system depends on
- Start with happy-path tests for all endpoints, then error cases
- Estimated gain: +15% overall coverage

### Round 2 — MCP tools (estimated 2-3 days)
Target: all MCP tool modules (currently 15-48%)
- Focus on `evolution.py`, `idea.py`, `hardware.py`, `task.py`
- Use FastAPI TestClient for integration tests
- Estimated gain: +10% overall coverage

### Round 3 — CLI & hooks (estimated 1-2 days)
Target: all zero-coverage modules
- CLI tools can be tested with subprocess or pytest's CLI runner
- Hooks need careful mocking of Claude Code environment
- Estimated gain: +8% overall coverage

### Round 4 — Edge cases & known failure
- Fix the 1 failing test: `test_client_disconnect_does_not_affect_others`
- Add connection cleanup tests to address the 17 SAWarning messages
- Estimated gain: +2% overall coverage

**Total estimated effort to reach 80%**: ~6-8 days of focused test writing.

## Known Issues Identified

1. **SQLAlchemy connection warnings** — 17 instances of "garbage collector is trying to clean up non-checked-in connection" — indicates pool lifecycle issues in test fixtures
2. **1 test failure** — `test_client_disconnect_does_not_affect_others` in WebSocket concurrent connection tests
3. **Template mismatch** — research-spike template created generic tasks unrelated to coverage analysis scope, confirming the pipeline template mismatch bug

## Next Steps

1. Run focused coverage on API route modules using targeted pytest markers
2. Address the SQLAlchemy connection cleanup warnings in test fixtures
3. Fix the flaky WebSocket disconnect test
4. Add integration tests for all 5 core CRUD endpoints (ideas, tasks, projects, pipelines, teams)
