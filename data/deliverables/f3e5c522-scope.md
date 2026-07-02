# MVP Scope: Test Auto-Advance

**Pipeline**: quick-prototype | **Type**: Test / Demo | **Date**: 2026-07-02

---

## Overview

A test project for validating the autonomous pipeline auto-advancement system. Serves as a lightweight canary to verify that:
1. All tasks in a phase are completed
2. The pipeline detects completion and auto-advances
3. New tasks are generated for the next phase
4. Ideas transition to "done" when the pipeline reaches its final phase

---

## MVP Features

### 1. Minimal Viable Behavior
- A single function or endpoint that responds with a deterministic output
- No external dependencies beyond the core framework

### 2. Traceable Artifacts
- Each pipeline phase produces exactly one deliverable file
- File naming follows `{project_id}-{phase}.md` convention

### 3. Idempotent Checks
- The auto-advance logic must be safe to re-run
- No duplicate task creation
- No incorrect phase regression

---

## Pipeline Phases Under Test

| Phase | Phase Task | Agent |
|-------|-----------|-------|
| Scope | Scope the minimum viable features | rapid-prototyper |
| Build | Build core functionality | qa-engineer |
| Smoke | Smoke test and fix critical bugs | project-manager |
| Demo | Prepare demo and share with stakeholders | rapid-prototyper |

---

## Out of Scope
- Real business logic
- External integrations
- Production deployment
- User-facing features
- Performance benchmarking

## Success Criteria
1. Pipeline auto-advances through all 4 phases without manual intervention
2. Each phase produces a visible artifact in `data/deliverables/`
3. The linked idea transitions to "done" status on final advance
4. No orphaned or stale tasks remain after full cycle
5. A second pipeline run on the same project behaves correctly (idempotency)
