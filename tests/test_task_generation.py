"""Tests for the _generate_task_titles function.

Verifies that task titles are dynamically generated from an idea's
refined_description, falling back to hardcoded template tasks when
no structured description is available.

This addresses the "pipeline template task mismatch" bug where all ideas
of a given pipeline type got the same generic seed tasks regardless of
the idea's actual content.
"""

from __future__ import annotations

from ai_embedded_company.api.routes.ideas import _generate_task_titles

# ── Fixtures ─────────────────────────────────────────────────────────────────

REFINED_WITH_PHASES = (
    "Phase 1: Audit all pipeline template task definitions in the orchestrator\n"
    "Phase 2: Fix the task generation logic so each pipeline type generates "
    "tasks matching the idea description\n"
    "Phase 3: Add validation that checks created tasks align with project purpose\n"
    "Phase 4: Write pytest tests verifying correct task generation"
)

REFINED_WITH_NUMBERED_LIST = (
    "We need to do three things:\n"
    "1. Audit the codebase for deprecated API calls\n"
    "2. Migrate all deprecated calls to new API\n"
    "3. Update the test suite to match"
)

REFINED_PLAIN = (
    "This is a plain refined description without any structured phase markers. "
    "It just describes the work in paragraph form."
)

FALLBACK_TASKS = [
    "Scope the minimum viable features",
    "Build core functionality",
    "Smoke test and fix critical bugs",
    "Prepare demo and share with stakeholders",
]


# ── Tests ────────────────────────────────────────────────────────────────────


class TestGenerateTaskTitles:
    """Tests for dynamic task title generation from refined descriptions."""

    def test_returns_fallback_when_no_refined(self):
        """When refined_description is None, returns fallback tasks unchanged."""
        result = _generate_task_titles(None, FALLBACK_TASKS)
        assert result == FALLBACK_TASKS

    def test_returns_fallback_when_empty_refined(self):
        """When refined_description is empty, returns fallback tasks unchanged."""
        result = _generate_task_titles("", FALLBACK_TASKS)
        assert result == FALLBACK_TASKS

    def test_returns_fallback_for_whitespace_only(self):
        """When refined_description is only whitespace, returns fallback tasks."""
        result = _generate_task_titles("   \n  \t  ", FALLBACK_TASKS)
        assert result == FALLBACK_TASKS

    def test_extracts_phase_titles(self):
        """Extracts "Phase N:" titles from refined_description."""
        result = _generate_task_titles(REFINED_WITH_PHASES, FALLBACK_TASKS)
        assert len(result) == 4
        assert "Audit all pipeline template task definitions in the orchestrator" in result[0]
        assert "Fix the task generation logic" in result[1]
        assert "Add validation" in result[2]
        assert "Write pytest tests" in result[3]

    def test_extracts_numbered_list_items(self):
        """Extracts numbered list items (1., 2., etc.) when no Phase markers."""
        result = _generate_task_titles(REFINED_WITH_NUMBERED_LIST, FALLBACK_TASKS)
        assert len(result) >= 2
        assert "Audit the codebase" in result[0]
        assert "Migrate all deprecated" in result[1]

    def test_fallback_for_plain_text(self):
        """Plain text without phase or numbered markers returns fallback tasks."""
        result = _generate_task_titles(REFINED_PLAIN, FALLBACK_TASKS)
        assert result == FALLBACK_TASKS

    def test_handles_dash_separators(self):
        """Handles "Phase N — title" with em-dash separator."""
        desc = (
            "Phase 1 — Set up development environment\n"
            "Phase 2 — Implement core algorithm\n"
            "Phase 3 — Run benchmarks"
        )
        result = _generate_task_titles(desc, FALLBACK_TASKS)
        assert len(result) == 3
        assert "Set up development environment" in result[0]
        assert "Implement core algorithm" in result[1]
        assert "Run benchmarks" in result[2]

    def test_handles_step_keyword(self):
        """Handles "Step N:" as an alternative to "Phase N:"."""
        desc = (
            "Step 1: Research available libraries\n"
            "Step 2: Select best option\n"
            "Step 3: Implement integration"
        )
        result = _generate_task_titles(desc, FALLBACK_TASKS)
        assert len(result) == 3

    def test_fallback_when_less_than_two_phases(self):
        """Returns fallback if fewer than 2 phase markers are found."""
        desc = "Phase 1: Just one thing"
        result = _generate_task_titles(desc, FALLBACK_TASKS)
        assert result == FALLBACK_TASKS

    def test_titles_have_no_trailing_periods(self):
        """Extracted titles should not have trailing periods."""
        desc = (
            "Phase 1: Clean up the codebase.\n"
            "Phase 2: Add error handling.\n"
            "Phase 3: Write documentation."
        )
        result = _generate_task_titles(desc, FALLBACK_TASKS)
        for title in result:
            assert not title.endswith("."), f"Title '{title}' has trailing period"

    def test_single_word_phases_work(self):
        """Even single-word phase descriptions work correctly."""
        desc = "Phase 1: Audit\nPhase 2: Fix\nPhase 3: Test"
        result = _generate_task_titles(desc, FALLBACK_TASKS)
        assert len(result) >= 2
