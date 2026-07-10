# Cycle #343 — Pipeline-Type Keyword Matching Refactor

**Date:** 2026-07-11

## Summary

Revived the **Pipeline-Type Matching Improvement** archived idea, executed its research-spike pipeline, and completed all 8 tasks. The core achievement was extracting the keyword matching logic from a nested endpoint function into testable module-level code, then rewriting the test file to import production functions directly instead of using stale replicas.

## What was done

1. **Extracted keyword constants and scoring logic** from `refine_idea()` in `ideas.py` into module-level `PIPELINE_KEYWORDS`, `PIPELINE_NEGATIVE_KEYWORDS`, `PIPELINE_TIEBREAKERS`, `score_pipeline_type()`, and `select_pipeline_type()` — pure functions that can be imported and tested without bootstrapping the web framework.

2. **Rewrote test file** (`tests/test_pipeline_keyword_matching.py`): replaced all stale replicas with direct imports from `ai_embedded_company.api.routes.ideas`. Added 12 new tests covering:
   - `research_negative` exclusion rules (backend/pipeline keywords exclude research-spike)
   - Evolution/antibody/self-improvement negative keyword coverage (verifies all 3 affected pipeline types)
   - `pipeline` / `pipeline-hardening` in negative lists
   - `suggested_hint` boosting
   - Constants consistency (every type has keywords + tiebreaker)
   - Quick-prototype scoring with its actual keyword list

3. **Verified backward compatibility**: all 234 tests pass (excluding pre-existing WS hang).

4. **Committed the changes** and advanced the pipeline through all phases to `done`.

## System state

- 0 raw ideas, 0 refined ideas
- 0 todo tasks
- 0 active pipelines
- 234 tests passing
- System fully drained
