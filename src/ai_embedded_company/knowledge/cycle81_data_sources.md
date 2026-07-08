# Cross-Cycle Pattern Synthesis — Academic Databases & Data Sources

## Internal Data Sources (Primary)

The cross-cycle analysis will primarily draw from the system's own operational data, accessible via the existing API:

| Endpoint | Data | Use Case |
|----------|------|----------|
| `/api/tasks/metrics` | Aggregated task stats (completion time, tokens, agent breakdown, status counts) | Trend analysis across cycles |
| `/api/tasks/?status=done` | Individual task records (elapsed minutes, agent, project) | Per-cycle performance distribution |
| `/api/ideas/` | Idea lifecycle (creation → refinement → pipeline → completion) | Conversion funnel analysis |
| `/api/pipelines/` | Pipeline phase durations and types | Phase bottleneck identification |
| `/api/evolution/status` | Failure records, antibodies, vaccines | Self-improvement effectiveness |
| `/api/prompts/templates/` | Optimized prompt templates | Template usage impact analysis |
| `/api/prompts/results/` | Actual usage stats per template | A/B experiment outcomes |

## External Academic Databases (Secondary — Future Reference)

When extending analysis beyond internal metrics:

| Database | Focus Area | Access |
|----------|-----------|--------|
| **IEEE Xplore** | Embedded systems, autonomous systems, self-adaptive software | Subscription |
| **ACM Digital Library** | Software engineering, autonomous agents, adaptive systems | Subscription |
| **arXiv (cs.SE, cs.AI)** | Latest research on self-improving AI systems, prompt optimization | Open access |
| **Google Scholar** | Broad literature search | Open access |
| **Semantic Scholar** | AI-powered research discovery with citation graphs | Open access |

## Key Metrics Framework

Metrics to collect per cycle for pattern synthesis:

```python
CYCLE_METRICS = {
    "tasks": {
        "completed": int,
        "avg_completion_minutes": float,
        "total_tokens": int,
        "by_agent": dict[str, int],      # role → count
        "by_priority": dict[str, int],    # high/medium/low → count
    },
    "ideas": {
        "conversion_rate": float,         # refined→pipeline→done
        "avg_idea_to_pipeline_hours": float,
        "by_tag": dict[str, int],
    },
    "pipelines": {
        "completed": int,
        "phase_durations": dict[str, float],  # phase → avg hours
        "by_type": dict[str, int],
    },
    "evolution": {
        "findings": int,
        "antibodies": int,
        "vaccines": int,
    },
}
```

---
*Generated during Cycle #81 — Autonomous execution*
