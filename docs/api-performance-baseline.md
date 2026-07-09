# API Performance Baseline Report

**Generated:** 2026-07-10 (Cycle #234)
**Project:** API Performance Profiling & Optimization

## Executive Summary

All API endpoints under test exhibit sub-30ms median latency, well within the <500ms threshold. Under concurrent load (10 parallel requests), p95 latency increases to ~100-170ms due to SQLite single-writer contention. One endpoint (`/api/teams/`) returns HTTP 500 — a serialization bug was identified and fix prepared.

## Methodology

- **Tool**: Python `urllib` concurrent profiling
- **Concurrency**: 10 parallel requests per endpoint
- **Metrics captured**: Min, p50, p95, p99, Max latency
- **Date**: 2026-07-10

## Latency Results

| Endpoint | Min(ms) | p50(ms) | p95(ms) | p99(ms) | Max(ms) | Status |
|---|---|---|---|---|---|---|
| /health | 1.7 | 2.9 | 103.5 | 103.5 | 103.5 | ✅ |
| /status | 4.7 | 9.5 | 102.1 | 102.1 | 102.1 | ✅ |
| /api/ideas/ | 6.3 | 18.0 | 106.9 | 106.9 | 106.9 | ✅ |
| /api/tasks/ | 11.1 | 19.1 | 97.6 | 97.6 | 97.6 | ✅ |
| /api/projects/ | 8.7 | 14.9 | 127.3 | 127.3 | 127.3 | ✅ |
| /api/pipelines/ | 4.6 | 15.2 | 116.8 | 116.8 | 116.8 | ✅ |
| /api/evolution/status | 3.8 | 6.7 | 169.1 | 169.1 | 169.1 | ✅ |
| /api/teams/ | — | — | — | — | — | ❌ 500 Error |

## Problems Found

### 1. `/api/teams/` — HTTP 500 Internal Server Error (HIGH)
- **Root cause**: The `Team` Pydantic response model expects `members: list[AgentRole]` (enum values), but the database stores members as `list[dict]` with `role` and `status` keys (`[{"role": "idea-refiner", "status": "idle"}, ...]`). FastAPI validation fails when trying to coerce a dict into an enum.
- **Fix prepared**: Created `TeamMemberInfo` type matching stored format; updated `_model_to_team` and `create_team` serialization. Changes are in `types.py` and `teams.py` — server restart required.

### 2. SQLite Connection Contention (MEDIUM)
- Under concurrent load (10 threads), p95 latency spikes from ~15ms to ~100-170ms across all endpoints. Root cause: SQLite's single-writer model creates contention on the connection pool. Mitigations:
  - Add connection pooling with `pool_size=5` and `max_overflow=10` to the async SQLite engine
  - Use `PRAGMA journal_mode=WAL` (Write-Ahead Logging) for concurrent reads
  - Consider read replicas or caching for read-heavy endpoints

### 3. Large Payload Sizes (LOW)
- `/api/tasks/` returns 81KB (all 160 tasks unfiltered)
- `/api/ideas/` returns 16KB
- **Recommendation**: Add pagination (`limit`/`offset`) and field filtering (`?fields=id,title,status`) to reduce payload sizes

## Payload Size Analysis

| Endpoint | Size | Recommendation |
|---|---|---|
| /api/tasks/ | 81,531 bytes | Add pagination, default limit=50 |
| /api/ideas/ | 16,185 bytes | Add pagination |
| /api/projects/ | 11,286 bytes | Add pagination |
| /api/pipelines/ | 6,097 bytes | OK |
| /api/teams/ | — | Fix 500 first |
| /api/evolution/status | 249 bytes | OK |

## Token & Task Metrics

- **Total tokens consumed (all time)**: 150,270
- **Total tasks tracked**: 44 (done)
- **Active tasks**: 0
- **Average completion time**: 3.6 min/task
- **Daily token trend**: 7/7 (19.7K), 7/8 (96.9K), 7/9 (33.7K)

## Recommendations

1. **Immediate**: Restart server to apply `/api/teams/` fix (types.py, teams.py changes)
2. **Short-term**: Add WAL mode (`PRAGMA journal_mode=WAL`) to SQLite engine for concurrent read performance
3. **Medium-term**: Add pagination to list endpoints (tasks, ideas, projects)
4. **Ongoing**: Set up periodic performance benchmarking (monthly)
