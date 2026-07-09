# Self-Healing Idle Detection System — MVP Scope

## Problem
Autonomous cycles frequently encounter fully idle states with no pending tasks, active pipelines, or unprocessed ideas. The system has no mechanism to self-recover from idle states.

## MVP Features

### 1. Idle State Detector (Priority: P0)
- Check at start of each cycle: scan tasks (pending=0), pipelines (active=0), ideas (new/refining=0)
- Classify idle depth: shallow (1-2 idle cycles), deep (3+ consecutive idle cycles)
- Log idle state to cycle report

### 2. Idea Revival Scorer (Priority: P0)
- Score archived ideas by: recency of creation, tag match to current system gaps, number of prior pipeline attempts
- Return top-3 candidates for auto-revival when deep idle detected

### 3. Auto-Seed Generator (Priority: P1)
- For deep idle: auto-create a maintenance/improvement idea
- Possible seed templates: "Database Health Checkup", "Dependency Version Audit", "Test Coverage Sweep"
- Each seeded idea gets `source: auto-seed` tag

### 4. Cycle Report Integration (Priority: P1)
- Append idle status section to each cycle report
- Include: cycles-idle count, revived ideas, auto-seeded ideas

## Out of Scope (v1)
- Machine learning for idea scoring
- External notification (email/Slack)
- Autonomous task execution

## Team
- rapid-prototyper: scope + core logic
- qa-engineer: testing
- project-manager: delivery

## Timeline
- Phase 1 (Idle Detector + Scorer): immediate
- Phase 2 (Auto-Seed + Report): after Phase 1 validated
