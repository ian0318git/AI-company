# Test Coverage Gap Report

Generated: 2026-07-10 | Cycle #332

## Overall Coverage: 42.7%
- Total statements: 4337
- Covered: 1853
- Missing: 2484

## Priority Gap Modules (Below 30%)

| Coverage | Missing | Module |
|----------|---------|--------|
| 0% | 102 | hooks/session_bootstrap.py |
| 0% | 89 | tools/connection_tester.py |
| 0% | 74 | cli/app.py |
| 0% | 49 | hooks/inject_context.py |
| 0% | 29 | hooks/guardrails.py |
| 0% | 29 | hooks/send_event.py |
| 0% | 21 | orchestrator/state.py |
| 0% | 17 | hooks/context_monitor.py |
| 0% | 17 | hooks/pre_compact_save.py |
| 0% | 1 | orchestrator/__init__.py |
| 15.4% | 137 | mcp/tools/evolution.py |
| 16.1% | 73 | mcp/tools/idea.py |
| 19.3% | 46 | mcp/tools/memory.py |
| 20.3% | 98 | mcp/tools/hardware.py |
| 21.2% | 41 | mcp/tools/code.py |
| 21.3% | 37 | mcp/_base.py |
| 23.5% | 39 | mcp/tools/guardrails.py |
| 26.2% | 62 | mcp/tools/task.py |
| 26.5% | 36 | mcp/tools/knowledge.py |
| 26.9% | 49 | mcp/_autostart.py |
| 28.0% | 67 | api/routes/dashboard.py |
| 29.2% | 323 | api/routes/ideas.py |
| 30.5% | 235 | api/routes/tasks.py |

## Top 5 Fill Plan
1. **orchestrator/state.py** — 0%, 21 lines, low complexity state machine
2. **hooks/guardrails.py** — 0%, 29 lines, isolated hook
3. **hooks/context_monitor.py** — 0%, 17 lines, isolated monitor
4. **hooks/pre_compact_save.py** — 0%, 17 lines, isolated hook
5. **mcp/tools/evolution.py** — 15.4%, expand by 50+ lines

Test suite: 246 passed, 1 warning
