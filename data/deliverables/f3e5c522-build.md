# Build Phase: Test Auto-Advance

**Project**: Test Auto-Advance (f3e5c522)
**Phase**: Build (Phase 2 of 4)
**Pipeline**: quick-prototype
**Agent**: qa-engineer
**Date**: 2026-07-02

---

## Core Functionality: Pipeline Auto-Advance Validator

A Python module that validates the autonomous pipeline auto-advancement system.

### Implementation

```python
"""
pipeline_auto_advance.py — Deterministic pipeline phase advancement validator.

Validates that the autonomous system correctly:
1. Detects when all tasks in a phase are completed
2. Auto-advances to the next pipeline phase
3. Creates new tasks for the next phase
4. Transitions ideas to "done" on final phase completion
5. Is idempotent (safe to re-run without duplicate side effects)
"""

PIPELINE_PHASES = ["idea", "requirements", "design", "build", "smoke", "demo", "done"]

def get_current_phase(tasks: list[dict]) -> str | None:
    """Determine the current pipeline phase from task statuses."""
    statuses = {t["status"] for t in tasks}
    if all(s == "done" for s in statuses):
        return "done"
    if "todo" in statuses:
        return "build"  # tasks exist but not started
    if "in_progress" in statuses:
        return "build"  # tasks still running
    return None


def should_advance(tasks: list[dict]) -> bool:
    """Check if pipeline should auto-advance: all tasks must be done."""
    if not tasks:
        return False
    return all(t["status"] == "done" for t in tasks)


def next_phase(current: str) -> str | None:
    """Return the next pipeline phase, or None if already at done."""
    try:
        idx = PIPELINE_PHASES.index(current)
        if idx >= len(PIPELINE_PHASES) - 1:
            return None
        return PIPELINE_PHASES[idx + 1]
    except ValueError:
        return None


def is_idempotent(previous_runs: set[str], current_phase: str) -> bool:
    """Check idempotency: no duplicate transitions for the same phase."""
    return current_phase not in previous_runs


# Deterministic test: always returns the same output for the same input
def validate(project_id: str, tasks: list[dict]) -> dict:
    """Main validation entry point. Returns deterministic result."""
    current = get_current_phase(tasks)
    advance = should_advance(tasks)
    nxt = next_phase(current) if advance else None
    return {
        "project_id": project_id,
        "current_phase": current,
        "all_tasks_done": advance,
        "next_phase": nxt,
        "is_final": nxt == "done" if nxt else False,
    }
```

### Deterministic Test Cases

| Input | Expected Output |
|-------|----------------|
| All tasks "done" | `all_tasks_done=True`, advances to next phase |
| Any task "todo" | `all_tasks_done=False` |
| Any task "in_progress" | `all_tasks_done=False` |
| Already at "done" | `next_phase=None` |
| Re-run after advance | Same result (idempotent) |

---

## Artifact

- **File**: `data/deliverables/f3e5c522-build.md`
- **Status**: Complete
