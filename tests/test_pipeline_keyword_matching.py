"""Tests for pipeline-type keyword matching logic.

Tests the module-level scoring and selection functions from ideas.py
directly (no replicas), ensuring that description + tag combinations
produce the expected pipeline type assignment.
"""

from __future__ import annotations

import pytest

from ai_embedded_company.api.routes.ideas import (
    PIPELINE_KEYWORDS,
    PIPELINE_NEGATIVE_KEYWORDS,
    PIPELINE_TIEBREAKERS,
    score_pipeline_type,
    select_pipeline_type,
)


# ── Tests ──────────────────────────────────────────────────────────────────


class TestBasicKeywordMatching:
    """Verify each pipeline type is selected by its own keywords."""

    def test_embedded_firmware_by_description(self):
        result = select_pipeline_type("Build firmware for ESP32 with I2C sensor", [])
        assert result == "embedded-firmware"

    def test_embedded_firmware_by_tags(self):
        result = select_pipeline_type("Some project", ["esp32", "sensor"])
        assert result == "embedded-firmware"

    def test_embedded_linux_by_description(self):
        result = select_pipeline_type("Linux kernel driver for BeagleBone", [])
        assert result == "embedded-linux"

    def test_web_fullstack_by_description(self):
        result = select_pipeline_type("Build a React dashboard with API backend", [])
        assert result == "web-fullstack"

    def test_web_fullstack_by_tags(self):
        result = select_pipeline_type("Some project", ["react", "frontend"])
        assert result == "web-fullstack"

    def test_quick_prototype_default(self):
        result = select_pipeline_type("Any random project idea", [])
        assert result == "quick-prototype"

    def test_research_spike_by_description(self):
        result = select_pipeline_type("Research report on market trends in 2025", [])
        assert result == "research-spike"

    def test_research_spike_by_chinese_keywords(self):
        result = select_pipeline_type("就業市場分析報告", [])
        assert result == "research-spike"

    def test_quick_prototype_by_maintenance_tag(self):
        """'maintenance' tags should match quick-prototype keywords."""
        result = select_pipeline_type("Clean up temp files", ["maintenance"])
        assert result == "quick-prototype"


class TestNegativeKeywords:
    """Verify negative keywords exclude inappropriate pipeline types."""

    def test_embedded_excluded_by_web_keyword(self):
        """'api' and 'backend' in description should exclude embedded-firmware."""
        result = select_pipeline_type("Build a backend API for sensor data", ["sensor"])
        assert result != "embedded-firmware", "sensor + api should not be embedded-firmware"

    def test_web_excluded_by_embedded_keyword(self):
        """'firmware' in description should exclude web-fullstack."""
        result = select_pipeline_type("Write firmware for a sensor", ["web"])
        assert result != "web-fullstack", "firmware keyword should exclude web-fullstack"

    def test_linux_excluded_by_embedded(self):
        result = select_pipeline_type("Arduino sensor project", ["linux"])
        assert result != "embedded-linux", "arduino keyword should exclude embedded-linux"

    def test_research_excluded_by_web_keyword(self):
        """'backend' in description should exclude research-spike."""
        result = select_pipeline_type("Build a backend API", ["research"])
        assert result != "research-spike", "backend keyword should exclude research-spike"

    def test_embedded_excluded_by_evolution_tag(self):
        """'evolution' tags should exclude embedded-firmware."""
        result = select_pipeline_type("Some idea", ["evolution", "self-improvement"])
        assert result != "embedded-firmware", "evolution tag should exclude embedded-firmware"

    def test_web_excluded_by_evolution_tag(self):
        """'evolution' tags should exclude web-fullstack."""
        result = select_pipeline_type("Some idea", ["evolution", "self-improvement"])
        assert result != "web-fullstack", "evolution tag should exclude web-fullstack"

    def test_research_excluded_by_evolution_tag(self):
        """'evolution' and 'pipeline' tags should exclude research-spike."""
        result = select_pipeline_type("Fix pipeline matching", ["evolution", "pipeline"])
        assert result != "research-spike", "pipeline keyword should exclude research-spike"


class TestTieBreaking:
    """Verify narrower matches beat broader ones."""

    def test_embedded_beats_linux(self):
        """Both embedded and linux keywords present — embedded is narrower."""
        result = select_pipeline_type("ESP32 embedded Linux driver", [])
        assert result == "embedded-firmware"

    def test_specific_beats_generic_research(self):
        """Concrete hardware keywords beat research keywords."""
        result = select_pipeline_type("Research report on ESP32 firmware", [])
        assert result == "embedded-firmware"


class TestBackendOnlyFallback:
    """Verify backend-only Python changes get quick-prototype, not web-fullstack."""

    def test_pure_backend_gets_quick_prototype(self):
        """Backend-only description with 'api' and 'backend' should get quick-prototype."""
        result = select_pipeline_type(
            "Fix the API endpoint for task listing", ["backend", "python"]
        )
        assert result == "quick-prototype", f"Expected quick-prototype, got {result}"

    def test_backend_with_frontend_stays_web(self):
        """Backend + frontend keywords should remain web-fullstack."""
        result = select_pipeline_type("Build a React frontend with FastAPI backend", [])
        assert result == "web-fullstack"

    def test_backend_only_python_with_fastapi(self):
        """FastAPI-only mention should get quick-prototype."""
        result = select_pipeline_type("Add a new FastAPI route for user auth", ["python"])
        assert result == "quick-prototype"


class TestEdgeCases:
    """Verify edge cases and boundary conditions."""

    def test_empty_description(self):
        result = select_pipeline_type("", [])
        assert result == "quick-prototype"

    def test_no_tags_no_keywords(self):
        result = select_pipeline_type("Just an idea", [])
        assert result == "quick-prototype"

    def test_conflicting_signals(self):
        """Multiple conflicting signals — should pick highest scoring."""
        result = select_pipeline_type("I2C sensor on M5Stack with React dashboard", [])
        assert result != "web-fullstack", "sensor keyword should exclude web-fullstack"
        assert result == "quick-prototype", "all specific pipelines excluded by negative keywords"

    def test_self_improvement_tag_not_web(self):
        """The original bug: 'self-improvement' and 'evolution' tags should not trigger web-fullstack."""
        result = select_pipeline_type(
            "Fix pipeline-type keyword matching heuristic",
            ["self-improvement", "evolution", "pipeline"],
        )
        assert result != "web-fullstack", "self-improvement/evolution tags should not trigger web-fullstack"
        assert result == "quick-prototype"

    def test_research_with_chinese_tags(self):
        result = select_pipeline_type("some project", ["研究", "分析"])
        assert result == "research-spike"

    def test_maintenance_tag_picks_quick_prototype(self):
        """'maintenance' tag excludes embedded-firmware. No other keywords → quick-prototype."""
        result = select_pipeline_type("Clean up root directory", ["maintenance"])
        assert result == "quick-prototype"

    def test_suggested_hint_boosts_winner(self):
        """A caller-supplied hint breaks ties toward the hinted type."""
        result = select_pipeline_type("Some vague idea", [], suggested_hint="web-fullstack")
        assert result == "web-fullstack"


class TestScoreFunction:
    """Direct tests of the scoring function itself."""

    def test_keyword_matches_add_points(self):
        score = score_pipeline_type(
            "firmware esp32 sensor", [], "embedded-firmware"
        )
        assert score > 5  # At least +6 from keywords + 5 tiebreaker

    def test_tag_matches_add_points(self):
        desc = "some desc"
        tags = ["esp32", "sensor"]
        score = score_pipeline_type(desc, tags, "embedded-firmware")
        assert score > 5  # At least +2 from tags + 5 tiebreaker

    def test_negative_excludes(self):
        score = score_pipeline_type("build a web api", [], "embedded-firmware")
        assert score == -999

    def test_negative_via_tag(self):
        score = score_pipeline_type("some project", ["frontend"], "embedded-firmware")
        assert score == -999

    def test_no_matches(self):
        score = score_pipeline_type("unrelated text", [], "embedded-firmware")
        assert score == 0

    def test_tiebreaker_breaks_ties(self):
        """Embedded has higher tiebreaker than linux when both match equally."""
        score_emb = score_pipeline_type("kernel driver for sensor", [], "embedded-firmware")
        score_lnx = score_pipeline_type("kernel driver for sensor", [], "embedded-linux")
        assert score_emb > score_lnx

    def test_quick_prototype_score_with_keywords(self):
        """quick-prototype scores from positive keywords like 'pipeline'."""
        score = score_pipeline_type("Fix pipeline matching", [], "quick-prototype")
        assert score > 0

    def test_research_negative_excludes_backend(self):
        """research-spike should be excluded when description has 'backend'."""
        score = score_pipeline_type("Build a backend API", [], "research-spike")
        assert score == -999


class TestConstantsConsistency:
    """Verify that the production constants are internally consistent."""

    def test_all_pipeline_types_have_keywords(self):
        """Every defined pipeline type must have a keyword list."""
        for ptype in ["embedded-firmware", "embedded-linux", "web-fullstack",
                       "research-spike", "quick-prototype"]:
            assert ptype in PIPELINE_KEYWORDS, f"{ptype} missing from PIPELINE_KEYWORDS"
            assert len(PIPELINE_KEYWORDS[ptype]) > 0, f"{ptype} has empty keyword list"

    def test_all_pipeline_types_have_tiebreakers(self):
        """Every defined pipeline type must have a tiebreaker."""
        for ptype in PIPELINE_KEYWORDS:
            assert ptype in PIPELINE_TIEBREAKERS, f"{ptype} missing from PIPELINE_TIEBREAKERS"

    def test_negative_keywords_cover_evolution_tags(self):
        """'self-improvement' and 'evolution' must be negative for web, embedded, and research."""
        for ptype in ["embedded-firmware", "web-fullstack", "research-spike"]:
            neg = PIPELINE_NEGATIVE_KEYWORDS.get(ptype, [])
            assert "self-improvement" in neg, f"{ptype} missing self-improvement in negatives"
            assert "evolution" in neg, f"{ptype} missing evolution in negatives"
            assert "antibody" in neg, f"{ptype} missing antibody in negatives"

    def test_pipeline_keyword_in_negatives(self):
        """'pipeline' must be negative for web-fullstack and research-spike."""
        for ptype in ["web-fullstack", "research-spike"]:
            neg = PIPELINE_NEGATIVE_KEYWORDS.get(ptype, [])
            assert "pipeline" in neg, f"{ptype} missing pipeline in negatives"
            assert "pipeline-hardening" in neg, f"{ptype} missing pipeline-hardening in negatives"


class TestApiRouteImportable:
    """Smoke tests that the API route and MCP tool modules are importable."""

    def test_api_route_importable(self):
        from ai_embedded_company.api.routes.ideas import refine_idea  # noqa: F811
        assert callable(refine_idea)

    def test_mcp_tool_importable(self):
        from ai_embedded_company.mcp.tools.idea import register_tools  # noqa: F811
        assert callable(register_tools)
