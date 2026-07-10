# API Documentation Sync — Audit Report
**Date:** 2026-07-11 07:26:11

## Summary
- OpenAPI endpoints: 51
- Source route files: 12
- Source routes: 45
- Matched: 6
- Schema-only: 45
- Source-only: 39

## Endpoint Cross-Reference

### Both (n=6)
  - ✅ /autonomous\n  - ✅ /autonomous/start\n  - ✅ /autonomous/stop\n  - ✅ /event\n  - ✅ /health\n  - ✅ /status\n

### Schema Only (n=45) — defined in OpenAPI but no matching source route
  - ⚠️ /api/dashboard/metrics\n  - ⚠️ /api/evolution/antibody-candidates\n  - ⚠️ /api/evolution/antibody-candidates/{candidate_id}/review\n  - ⚠️ /api/evolution/classify\n  - ⚠️ /api/evolution/failures\n  - ⚠️ /api/evolution/monitor\n  - ⚠️ /api/evolution/recommend\n  - ⚠️ /api/evolution/research\n  - ⚠️ /api/evolution/status\n  - ⚠️ /api/ideas\n  - ⚠️ /api/ideas/{idea_id}\n  - ⚠️ /api/ideas/{idea_id}/archive\n  - ⚠️ /api/ideas/{idea_id}/deliverables\n  - ⚠️ /api/ideas/{idea_id}/deliverables/{filename}\n  - ⚠️ /api/ideas/{idea_id}/deliverables/{filename}/html\n  - ⚠️ /api/ideas/{idea_id}/refine\n  - ⚠️ /api/ideas/{idea_id}/start\n  - ⚠️ /api/ideas/{idea_id}/team/add-agent\n  - ⚠️ /api/ideas/{idea_id}/team/remove-agent\n  - ⚠️ /api/ideas/{idea_id}/workflow\n

### Source Only (n=39) — defined in source but not in OpenAPI
  - 🔧 \n  - 🔧 /antibody-candidates\n  - 🔧 /antibody-candidates/{candidate_id}/review\n  - 🔧 /classify\n  - 🔧 /experiments\n  - 🔧 /experiments/{test_id}\n  - 🔧 /experiments/{test_id}/conclude\n  - 🔧 /failures\n  - 🔧 /insights\n  - 🔧 /insights/generate\n  - 🔧 /metrics\n  - 🔧 /monitor\n  - 🔧 /optimized\n  - 🔧 /recommend\n  - 🔧 /research\n  - 🔧 /results\n  - 🔧 /roi\n  - 🔧 /templates\n  - 🔧 /templates/{template_id}\n  - 🔧 /token-history\n

## Source Files
  - routes/dashboard.py (1 routes)\n  - routes/evolution.py (8 routes)\n  - routes/ideas.py (12 routes)\n  - routes/pipelines.py (4 routes)\n  - routes/projects.py (6 routes)\n  - routes/prompts.py (14 routes)\n  - routes/system.py (6 routes)\n  - routes/tasks.py (8 routes)\n  - routes/teams.py (3 routes)\n
