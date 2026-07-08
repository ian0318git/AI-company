# Wire Prompt Templates into Task Execution — Schema & API Design

## System State Analysis

### Existing Schema (Already Implemented)
The prompt optimization infrastructure is already in place:

| Table | Purpose | Status |
|-------|---------|--------|
| `prompt_templates` | Stores optimized prompt templates per agent role | ✅ Exists |
| `prompt_results` | Logs results (tokens, time) when template is used | ✅ Exists |
| `ab_experiments` | A/B experiment control/variant tracking | ✅ Exists |
| `optimization_insights` | Auto-generated optimization recommendations | ✅ Exists |
| `tasks.prompt_template_id` | FK linking a task to its template | ✅ Exists |

### Injection Flow (Partially Implemented)
The bridge endpoints exist in `tasks.py`:
1. **`_inject_prompt_optimization()`** — Called at task creation. Queries `prompt_templates` for the best active template matching the task's agent role. Prepends template body to task description.
2. **`_log_prompt_result()`** — Called when task completes (`status=done`). Logs tokens_used and elapsed time to `prompt_results`.
3. **Task model** already has `prompt_template_id` to link back.

### API Contracts (Already Available)

```
POST /api/tasks/ → {assigned_agent, ...}
  └─ Injects prompt template if one exists for the agent role

PATCH /api/tasks/{id}/status?status=done
  └─ Logs prompt result (tokens, completion time)

POST /api/tasks/{id}/tokens → {"tokens": N, "agent": "role"}
  └─ Accumulates token usage for result logging

GET /api/prompts/templates/?agent_role=X
  └─ Lists active templates for a role

POST /api/prompts/experiments/
  └─ Creates A/B experiment

GET /api/prompts/insights/
  └─ Returns optimization insights
```

### Gap Analysis

| Gap | Impact | Recommendation |
|-----|--------|---------------|
| No agent ever assigned to tasks | `_inject_prompt_optimization` skips when `assigned_agent` is None | Assign agents at task creation |
| A/B experiments have 0 samples each | `experiment_id` not wired through | Add experiment_id to task creation payload |
| No fallback when no template exists | Falls back to stock prompt gracefully | Already handled — no change needed |
| Prompt results logged but not aggregated | No dashboard to view template performance | Handled by Prompt Optimization Dashboard (separate idea) |

### Recommended Next Steps

1. **Agent assignment** — When creating tasks in the pipeline auto-task-generator, include `assigned_agent` in the payload so template injection activates.
2. **Experiment wiring** — Pass `experiment_id` through the task lifecycle so A/B experiments accumulate samples.
3. **Dashboard integration** — Surface template performance stats (avg tokens, avg time) from `prompt_results` in the existing dashboard.

---
*Generated during Cycle #81 — Autonomous execution*
