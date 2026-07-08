# Evolution System Enhancement — API & Data Model Spec

## Database Schema (SQLite extension)

```sql
-- Categorized failure patterns
CREATE TABLE evolution_antibodies (
    id TEXT PRIMARY KEY,
    pattern_name TEXT NOT NULL UNIQUE,
    description TEXT,
    category TEXT NOT NULL,          -- timeout | budget | api_error | logic_error
    trigger_condition TEXT,          -- e.g. "task runtime > 3x estimate"
    preventive_action TEXT,          -- e.g. "add retry with backoff"
    hit_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_triggered_at TIMESTAMP
);

-- Optimization recipes from fast cycles
CREATE TABLE evolution_vaccines (
    id TEXT PRIMARY KEY,
    recipe_name TEXT NOT NULL UNIQUE,
    description TEXT,
    pipeline_type TEXT,              -- which pipeline this applies to
    success_pattern TEXT,            -- what made it fast
    avg_time_saved_minutes REAL,
    applied_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Per-idea performance tracking for recommendations
CREATE TABLE evolution_idea_performance (
    id TEXT PRIMARY KEY,
    idea_category TEXT NOT NULL,      -- autonomous | dashboard | embedded | research
    pipeline_type TEXT NOT NULL,
    total_cycles INTEGER DEFAULT 0,
    completion_rate REAL DEFAULT 0.0, -- 0.0 - 1.0
    avg_completion_minutes REAL,
    avg_tokens_used INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## New API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/evolution/recommend` | Suggests next best idea type + pipeline template |
| `POST` | `/api/evolution/antibodies` | Register a new antibody pattern |
| `GET` | `/api/evolution/antibodies` | List all antibodies with hit counts |
| `POST` | `/api/evolution/vaccines` | Register a new vaccine recipe |
| `GET` | `/api/evolution/vaccines` | List all vaccines |
| `GET` | `/api/evolution/performance` | Per-category performance analytics |

## Recommendation Algorithm (v1)

```
score(category) = 
    completion_rate * 0.4 
    + (1 - (avg_completion_minutes / max_completion_minutes)) * 0.3 
    + (1 - (avg_tokens / max_tokens)) * 0.3

Pick category with highest score → return its best pipeline_type
```

## React Components

```
EvolutionPanel
├── AntibodyList         — Table of failure patterns with hit counts
│   └── AntibodyRow      — Pattern name, category, times triggered, action
├── VaccineList          — Optimization recipes with time-saved metric
│   └── VaccineRow       — Recipe name, pipeline type, avg time saved
├── PerformanceChart     — Grouped bar: completion rate by category
├── RecommendationCard   — "Next: try a [category] idea with [pipeline]" 
└── HealthIndicator      — Traffic-light: healthy / degraded / nascent
```
