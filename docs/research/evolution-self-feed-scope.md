# Evolution Self-Feed: Research Scope

## Problem Statement

The evolution system has antibodies and failure records but **no automated feedback loop** feeds cycle outcomes into the evolution tables. Each autonomous cycle produces outcomes (failures, successes, patterns) that should seed the evolution database — closing the loop between execution and system improvement.

## Research Questions

1. What failure patterns from autonomous cycles are worth capturing?
2. How should failure patterns be classified and stored in the existing evolution schema?
3. What is the optimal trigger mechanism: post-cycle hook, periodic cron, or on-demand CLI?
4. How do we deduplicate failure records across cycles?
5. What metadata (cycle number, timestamp, severity, component) is needed for effective antibody generation?

## Scope Boundaries

| In Scope | Out of Scope |
|----------|--------------|
| Post-cycle hook design | Real-time failure ingestion during a cycle |
| Schema mapping: cycle outcomes → evolution tables | Frontend UI for evolution data |
| CLI command prototype (run post-cycle) | Full automation infrastructure |
| Analysis of existing cycle reports (cycle-243 to 247) | Cross-cycle ML-based pattern detection |
| Antibody generation trigger from new failure records | Integration with external observability tools |

## Methodology

1. Audit existing evolution schema (tables: `failure_records`, `antibody_candidates`, `event_logs`)
2. Analyze recent cycle reports to extract representative failure patterns
3. Design mapping between cycle outcome signals and evolution table records
4. Prototype a CLI command that reads cycle output and seeds the database
5. Test with simulated cycle outcomes

## Success Criteria

- CLI command successfully reads a cycle report and inserts ≥1 failure record
- Failure records trigger antibody candidate generation
- Zero schema changes required (work within existing tables)
- Round-trip test: insert → antibody_generated → verify
