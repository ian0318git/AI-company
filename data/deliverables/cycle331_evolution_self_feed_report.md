# Cycle Evolution Self-Feed — Auto-Ingest Failure Patterns

## Executive Summary

This report documents the design and implementation of a post-cycle hook that extracts failure patterns from autonomous cycle outcomes and seeds them into the evolution database tables. Prior to this work, the evolution system was never fed despite many completed autonomous cycles, leaving a gap where failure patterns were observed but never systematically captured and acted upon.

## Architecture

### Components

1. **Failure Extractor** — Scans completed cycle artifacts for:
   - Task failures (status changes, error messages)
   - Pipeline stalls (phases that exceeded expected duration)
   - Error logs and exception traces
   - Completion anomalies (partial completions, skipped phases)

2. **Evolution Mapper** — Maps extracted failures to evolution database tables:
   - `evolution_failures` — Raw failure events with context
   - `evolution_antibody_candidates` — Repeated failure patterns → antibody candidates
   - `evolution_research` — Novel failure patterns → research topics

3. **Auto-Seed Engine** — Triggers after each completed cycle:
   - Checks for new failure data
   - Deduplicates against existing records
   - Seeds high-value patterns into the evolution pipeline
   - Generates antibody candidates for recurring failures

### Data Flow

```
Cycle Completion → Failure Extraction → Pattern Analysis → Dedup Check
    ↓
Evolution Tables (failures / antibodies / research)
    ↓
Next Cycle: Evolution Status Check → Prioritized Improvements
```

## Key Findings

### 1. Common Failure Patterns Identified

Analysis of past cycles revealed these recurring failure modes:
- **Pipeline template mismatch** — Tasks created with generic templates unrelated to the idea (3+ occurrences)
- **Auto-seed duplication** — "Revived: Revived:" prefix bug from re-reviving already-revived ideas
- **Task description gaps** — Empty task descriptions for pipeline-created tasks
- **Session expiry** — SQLAlchemy session expiry causing lazy-load failures

### 2. Gap Analysis

| Gap | Impact | Priority |
|-----|--------|----------|
| No post-cycle hook exists | 100% of cycle outcomes uncaptured | Critical |
| Evolution tables have no auto-feed | System cannot learn from failures | Critical |
| Manual triggering required | Requires human intervention each cycle | High |
| No dedup mechanism | Duplicate entries waste resources | Medium |

## Implementation Plan

### Phase 1: Post-Cycle Hook (completed)
- Design hook interface that fires after pipeline advance completes
- Extract structured data from cycle artifacts

### Phase 2: Evolution DB Integration (completed)
- Map failure patterns to existing evolution table schemas
- Create insertion routines with dedup

### Phase 3: Auto-Seed (completed)
- Wire hook into the autonomous cycle completion flow
- Add cycle-count tracking to measure feed frequency

### Phase 4: Monitoring (completed)
- Add metrics to track evolution feed health
- Verify with test cycle that feed loop works end-to-end

## Verification

The end-to-end flow was verified by:
1. Completing a full autonomous cycle
2. Confirming failure data appears in evolution tables
3. Confirming antibody candidates are generated from recurring patterns
4. Measuring cycle-count delta between feeds

## Recommendations

1. **Enable auto-feed by default** — All autonomous cycles should feed into evolution
2. **Add dashboard widget** — Show evolution feed status on the main dashboard
3. **Tune dedup sensitivity** — Adjust dedup threshold to prevent pattern flooding
4. **Archive stale candidates** — Auto-archive antibody candidates older than 30 days

---

*Generated for Cycle #331 — Evolution Self-Feed Initiative*
