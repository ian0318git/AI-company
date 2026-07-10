# Cycle #261 — Evolution Antibody Implementation: 3 Pipeline Hardening Fixes

**Generated:** 2026-07-10 13:22

## Summary

Created a new idea from evolution system antibody candidates, implemented 3 concrete code changes that harden the pipeline lifecycle against the most frequent failure patterns. Cycle broke the 5-cycle idle streak by generating fresh work from the evolution system's own findings rather than relying on archived idea revival.

## What Was Done

1. **Created and refined new idea from evolution system antibodies** — Scanned the 8 approved antibody candidates and synthesized a new idea ("Implement Top Evolution Antibodies") targeting the top 3 pipeline-hardening fixes. Idea was refined with detailed phased implementation plan and started via `quick-prototype` pipeline.

2. **Project completion guard (projects.py:188-202)** — Added task-completion check before allowing a project's status to be set to `"completed"` via PATCH. Now returns 409 Conflict with a clear message listing orphan task count instead of silently completing with undone work.

3. **Pipeline full auto-advance fix (tasks.py:738-754)** — Fixed `_auto_advance_if_all_done` to loop-advance through ALL remaining phases up to "done" when all tasks are complete, instead of advancing only one phase and leaving the pipeline stuck (the root cause of the "Pipeline steps not auto-advanced" failure pattern observed 12 times across prior cycles).

4. **Idea refinement gate (ideas.py:657-665)** — Added guard in `start_idea` requiring `refined_description` to be non-null before starting a pipeline. Returns 400 with a pointer to the refine endpoint, preventing unrefined ideas from entering execution (failure pattern observed 10 times).

5. **Pipeline advance project guard (pipelines.py:126-136)** — When manually advancing a pipeline to "done", the endpoint now checks for orphan tasks before auto-completing the project, keeping it "active" if undone tasks remain.

## System State

| Metric | Value |
|--------|-------|
| Ideas | 38 (1 new, 26 done, 11 archived) |
| Tasks | 200 (0 pending, 0 in_progress, 200 done) |
| Pipelines | 50 (50 finished) |
| DB integrity | ok |
| Tests | 196 passed (no regressions) |

## Antibody-to-Code Mapping

| Antibody | Severity | Frequency | Implementation |
|----------|----------|-----------|----------------|
| Completed projects with orphan todo tasks | medium | 4 | `projects.py` completion guard + `pipelines.py` advance check |
| Pipeline steps not auto-advanced after creation | medium | 12 | `tasks.py` loop-advance to done |
| Ideas with null refined_description started pipelines | low | 10 | `ideas.py` refinement gate on start_idea |

## Notes

- All 196 existing tests pass with no regressions
- The auto-generated `web-fullstack` pipeline tasks (UI wireframes, frontend build, etc.) were not the right fit for a pure backend change — the pipeline template system generated them because the heuristic keyword matching chose "web-fullstack" over "quick-prototype" due to tags containing "evolution" and "self-improvement". Consider improving pipeline-type matching for non-hardware, non-research ideas.
