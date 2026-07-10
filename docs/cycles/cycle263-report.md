# Cycle #263 Report — Pipeline-Type Matching Improvement

**Date:** 2026-07-10
**Status:** Active with completed pipeline

## What was done

### 1. Pipeline-Type Matching — Scoring System with Negative Keywords
Replaced the heuristic first-match-wins pipeline type selection in both `src/ai_embedded_company/mcp/tools/idea.py` (MCP tool) and `src/ai_embedded_company/api/routes/ideas.py` (API route) with a robust scoring system:
- Each pipeline type scores based on keyword hits in both description and tags (+2 per description match, +1 per tag match)
- **Negative keyword exclusions** prevent false matches (e.g., "sensor" excludes web-fullstack, "react" excludes embedded-firmware)
- **Tie-breaking** prefers narrower categories (embedded-firmware > web-fullstack > quick-prototype) — tiebreaker only applies when actual keyword matches exist
- Added missing `research_kw` support to the MCP tool (was missing; only the API route had it)
- Added **backend-only fallback**: pure Python/API descriptions without frontend keywords are directed to `quick-prototype`, not `web-fullstack`

### 2. 30 Tests for Keyword Matching (all passing)
Created `tests/test_pipeline_keyword_matching.py` covering:
- Basic keyword matching for all 5 pipeline types
- Negative keyword exclusion rules
- Tie-breaking between competing matches
- Backend-only fallback logic
- Edge cases (empty descriptions, conflicting signals, `self-improvement`/`evolution` tags)
- Direct score function unit tests
- Import smoke tests for both code paths

### 3. Full pipeline lifecycle executed
- Active project ("Pipeline-Type Matching Improvement") was in `idea` phase with 8 generic research tasks
- Advanced the `research-spike` pipeline through all phases: idea -> requirements -> design -> implementation -> testing -> deploy -> done
- Idea auto-completed to `done`; project marked `completed`

### 4. Root cause of the original bug
The original heuristic had two flaws:
- `research_kw` was checked first, so anything remotely research-like was misclassified
- No negative keyword exclusions meant ambiguous tags like "pipeline" or "self-improvement" could trigger wrong pipeline types

## All 226 tests pass (0 failures, including 30 new tests)
