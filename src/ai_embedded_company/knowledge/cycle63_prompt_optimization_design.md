# Prompt Optimization Engine — Design Specification

## Overview

The autonomous system has completed 169 tasks across 36 pipelines with an average 2.6 min cycle time. Agent prompts are currently stock templates with no data-driven optimization. This engine systematically improves prompt effectiveness by analyzing real task execution data.

## Database Schema

### PromptTemplateModel
| Field | Type | Description |
|-------|------|-------------|
| id | UUID (PK) | Unique identifier |
| agent_role | str | Target agent (tech-lead, technical-writer, etc.) |
| pipeline_type | str | Pipeline this template applies to (or "any") |
| template_name | str | Human-readable name (e.g., "v1-stock", "v2-concise") |
| template_body | text | Actual prompt template with {variables} |
| token_count | int | Estimated token count of template |
| version | int | Monotonic version number |
| status | str | active / deprecated / testing |
| created_at | datetime | |
| updated_at | datetime | |

### ABTestModel
| Field | Type | Description |
|-------|------|-------------|
| id | UUID (PK) | |
| experiment_name | str | "prompt-length-tl", "instruction-style-tw" |
| control_template_id | UUID (FK → PromptTemplateModel) | |
| variant_template_id | UUID (FK → PromptTemplateModel) | |
| target_agent_role | str | Agent role being tested |
| target_task_types | text | JSON array of matching task title patterns |
| sample_size_target | int | Tasks needed per arm |
| status | str | running / complete / cancelled |
| started_at | datetime | |
| completed_at | datetime | |

### PromptResultModel
| Field | Type | Description |
|-------|------|-------------|
| id | UUID (PK) | |
| task_id | UUID (FK → TaskModel) | Task this result came from |
| template_id | UUID (FK → PromptTemplateModel) | Which template was used |
| a_b_test_id | UUID (nullable, FK → ABTestModel) | Optional test this was part of |
| arm | str | "control" or "variant" |
| tokens_used | int | Actual tokens consumed by the task |
| completion_seconds | float | Task execution time |
| task_status | str | done / failed / blocked |
| agent_role | str | Which agent executed |
| created_at | datetime | |

### OptimizationInsightModel
| Field | Type | Description |
|-------|------|-------------|
| id | UUID (PK) | |
| agent_role | str | |
| finding | text | "Shorter instructions (under 500 tokens) speed completion by 40%" |
| effect_size | float | Impact metric (e.g., 0.4 for 40% faster) |
| confidence | float | 0.0–1.0 statistical confidence |
| recommendation | text | Actionable change to make |
| source_task_count | int | How many tasks this insight is drawn from |
| created_at | datetime | |

## API Contracts

### POST /api/prompts/templates
Create a new prompt template.
```json
{
  "agent_role": "tech-lead",
  "pipeline_type": "any",
  "template_name": "v2-concise",
  "template_body": "You are a tech lead...",
  "token_count": 450
}
```

### GET /api/prompts/optimized
Get the best prompt template for a given context. Returns the highest-performing active template. Accepts query params: `agent_role`, `pipeline_type`, `task_title`.

### GET /api/prompts/experiments
List all A/B test experiments with results. Accepts `status` filter.

### POST /api/prompts/experiments
Start a new A/B test experiment.

### POST /api/prompt-results
Log a prompt execution result (called by the task runner after each task completes).

### GET /api/prompts/insights
Return data-driven optimization insights drawn from accumulated results.

### GET /api/prompts/roi
Return cost/benefit analysis: token savings per cycle, template improvement velocity.

## Integration Points

1. **Task creation hook**: When a new task is created, query `/api/prompts/optimized` and inject the optimized prompt
2. **Task completion hook**: After a task completes, call `/api/prompt-results` to log results
3. **Evolution system feed**: Insights pushed to `/api/evolution/research/findings` periodically
4. **Dashboard**: New tab showing prompt experiment results and token savings

## Success Metrics

- At least 15% reduction in tokens per task within 3 cycles
- At least 20% improvement in task completion speed for optimized agent roles
- Statistical significance (p < 0.05) in A/B tests before declaring a winner
- Zero regressions in task quality/completion rate when switching templates
