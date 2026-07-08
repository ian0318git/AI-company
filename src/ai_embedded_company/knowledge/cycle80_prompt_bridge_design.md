# Prompt Optimization Bridge — Architecture Design

## Problem
7 prompt templates exist across 5+ agent roles with zero usage. 4 A/B experiments completed with 0 samples each. The prompt optimization API exists but nothing wires it into task execution.

## Design

### Integration Point: Task Creation (`POST /api/tasks/`)

The `create_task` endpoint in `tasks.py` already has an evolution vaccine injection hook. Add a **prompt optimization enrichment** step alongside it:

```
TaskCreation(request)
  │
  ├─► Evolution vaccine injection (existing)
  │     └─► prepend vaccine warning to description
  │
  ├─► Prompt optimization enrichment (NEW)
  │     ├─► IF assigned_agent is set:
  │     │     GET /api/prompts/optimized?agent_role={assigned_agent}
  │     │     ├─► template found → prepend template_body to description
  │     │     └─► no template → skip (graceful degradation)
  │     └─► Store template_id on task metadata
  │
  └─► Create task in DB
```

### Integration Point: Task Completion (`PATCH .../status?status=done`)

```
TaskComplete(task_id, status=done)
  │
  ├─► Update task status (existing)
  │
  └─► Log prompt result to A/B system (NEW)
        └─► POST /api/prompts/results
              {
                "template_id": <stored template_id>,
                "experiment_id": null,
                "tokens_used": <task.tokens_used>,
                "completion_time_seconds": <calculated>,
                "agent_role": <task.assigned_agent>,
                "task_id": <task.id>
              }
```

### Integration Point: Task Token Logging (`POST /api/tasks/{task_id}/tokens`)

Already exists — agents report token consumption. Wire this into prompt metrics:
- After logging tokens, update the associated prompt template's avg_tokens if a template_id was stored.

### Sequence Flow

```
                  Task Creation                     Task Execution               Task Completion
                       │                                 │                            │
  ┌────────────────────▼────────────────────┐             │                            │
  │ 1. GET /api/prompts/optimized?role=X    │             │                            │
  │ 2. Prepend template_body to description  │             │                            │
  │ 3. Store template_id on task metadata    │             │                            │
  └────────────────────┬────────────────────┘             │                            │
                       │                                  │                            │
                       │   Task assigned to agent          │                            │
                       │   Agent reads enriched desc       │                            │
                       │   Agent works...                  │                            │
                       │   Agent POSTs /tokens             │                            │
                       │                                  │                            │
                       │                                  ├─► POST /api/tasks/{id}/tokens
                       │                                  │       └─► Also update template stats
                       │                                  │                            │
                       │                                  │           Task done        │
                       │                                  │                            ├─► PATCH status=done
                       │                                  │                            │       └─► POST /api/prompts/results
                       ▼                                  ▼                            ▼
```

### Data Model Changes

Add `prompt_template_id` field to Task model (nullable varchar):
- Set at task creation when template is applied
- Read at task completion to log results

### Fallback Behavior
- No template for role → skip enrichment (task proceeds normally)
- Optimized endpoint down → skip enrichment (catch exception, log warning)
- No template_id stored → skip result logging (no data loss)

### API Contracts

| Direction | Method | Endpoint | Purpose |
|-----------|--------|----------|---------|
| Task → Prompts | GET | /api/prompts/optimized?agent_role=X | Fetch best template |
| Task → Prompts | POST | /api/prompts/results | Log execution result |
| Task → Prompts | GET | /api/prompts/templates/{id} | Get template details |
| Agent → Task | POST | /api/tasks/{id}/tokens | Report token usage |

### A/B Experiment Integration

When an A/B experiment is active for a role:
- Control arm: use default template
- Variant arm: use experiment template
- Assignment: deterministic hash of task_id to ensure consistency
- Result logged to experiment via experiment_id in results payload

This design closes the prompt optimization feedback loop using existing API infrastructure with zero new endpoints and minimal code changes.
