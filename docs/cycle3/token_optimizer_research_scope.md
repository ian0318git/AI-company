# Agent Token Budget Optimizer — Research Scope

## Research Questions

1. **Current state**: What is the actual token consumption per task, per agent role, per pipeline type in the existing system?

2. **Budget allocation**: What is a reasonable soft/hard token budget per autonomous cycle given the project's usage patterns?

3. **Escalation triggers**: At what token threshold should the system (a) switch to a cheaper model, (b) fork a sub-task, or (c) request human approval?

4. **Cost prediction**: Can we predict total token cost of an idea based on its pipeline type and tags before execution?

5. **Evolution feedback**: How should over-budget tasks feed findings into the evolution system?

## Scope Boundaries

| In Scope | Out of Scope |
|----------|--------------|
| Per-agent token tracking via `/api/tasks/{id}/tokens` | Direct API billing / invoice integration |
| Soft/hard caps with model downgrade escalation | Multi-provider cost comparison (Anthropic vs OpenAI) |
| Cycle-level token accumulation & reporting | Real-time token streaming mid-agent-call |
| Evolution system integration (findings for over-budget tasks) | Token caching between identical agent prompts |

## Methodology

1. **Data collection**: Instrument the existing `/api/tasks/{task_id}/tokens` endpoint to capture prompt/completion tokens per agent call
2. **Baseline measurement**: Run 3-5 test ideas through the pipeline, record per-task and per-cycle totals
3. **Budget formula**: `budget = avg(token_per_task) * num_tasks * safety_multiplier(1.3)`
4. **Escalation policy**:
   - < 80% of budget → continue normally
   - 80-100% → switch agent model to lower tier
   - > 100% → fork remaining sub-tasks, log evolution finding

## Deliverables
- Token consumption baseline report
- Budget calculator implementation (Python module)
- API extension for budget endpoints
- Migration guide for existing pipelines
