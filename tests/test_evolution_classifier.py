"""Tests for the failure classification engine."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ai_embedded_company.evolution.classifier import (
    _classify_failure,
    _generate_antibody,
    _generate_vaccine,
    FAILURE_CATEGORIES,
    ANTIBODY_TEMPLATES,
    VACCINE_TEMPLATES,
)
from ai_embedded_company.storage.models import FailureRecord


def _make_record(
    title: str = "test",
    description: str = "",
    root_cause: str = "",
    category: str = "unknown",
    agent_role: str = "test-agent",
) -> FailureRecord:
    """Helper to create a minimal FailureRecord for testing."""
    return FailureRecord(
        id="test-id",
        title=title,
        description=description,
        root_cause=root_cause,
        category=category,
        agent_role=agent_role,
        status="reported",
        frequency=1,
        severity="medium",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestClassifyFailure:
    """Unit tests for _classify_failure heuristic."""

    def test_config_miss_detection(self):
        record = _make_record(
            description="Config file not found at /etc/app/config.yml",
            root_cause="Missing environment variable DATABASE_URL",
        )
        result = _classify_failure(record)
        assert result == "config_miss", f"Expected config_miss, got {result}"

    def test_dependency_detection(self):
        record = _make_record(
            description="ImportError: No module named 'requests'",
            root_cause="Missing pip package: requests==2.28.0",
        )
        result = _classify_failure(record)
        assert result == "dependency", f"Expected dependency, got {result}"

    def test_logic_error_detection(self):
        record = _make_record(
            description="TypeError: unsupported operand type(s) for +: 'int' and 'NoneType'",
        )
        result = _classify_failure(record)
        assert result == "logic_error", f"Expected logic_error, got {result}"

    def test_timeout_detection(self):
        record = _make_record(
            title="Slow task: Build firmware",
            description="Task took 45 minutes, exceeding threshold of 30 minutes.",
            root_cause="Task exceeded time threshold: 45 min vs 30 min threshold",
        )
        result = _classify_failure(record)
        assert result == "timeout", f"Expected timeout, got {result}"

    def test_api_error_detection(self):
        record = _make_record(
            description="HTTP 503 Service Unavailable from api.github.com",
            root_cause="API request failed after 3 retries",
        )
        result = _classify_failure(record)
        assert result == "api_error", f"Expected api_error, got {result}"

    def test_resource_exhaustion(self):
        record = _make_record(
            description="MemoryError: out of memory",
            root_cause="OOM killer terminated process with 2GB RSS",
        )
        result = _classify_failure(record)
        assert result == "resource", f"Expected resource, got {result}"

    def test_security_detection(self):
        record = _make_record(
            description="Authentication failed: invalid API token",
            root_cause="Permission denied for user 'bot' on resource /api/v2/deploy",
        )
        result = _classify_failure(record)
        assert result == "security", f"Expected security, got {result}"

    def test_pipeline_detection(self):
        record = _make_record(
            description="Cannot advance phase: step 'testing' is still in progress",
            root_cause="Pipeline phase ordering violated: deploy started before testing completed",
        )
        result = _classify_failure(record)
        assert result == "pipeline", f"Expected pipeline, got {result}"

    def test_unknown_failure_returns_none(self):
        record = _make_record(
            description="Something completely random happened with no keywords at all",
            root_cause="Mysterious error 0xDEADBEEF",
        )
        result = _classify_failure(record)
        # "random", "happened", "mysterious" etc. are not in any keyword list
        assert result is None, f"Expected None, got {result}"

    def test_multiple_matches_picks_highest_score(self):
        record = _make_record(
            description="ImportError: No module named 'requests'. Also, timeout occurred after 30s.",
            root_cause="Missing pip package and connection to pypi.org timed out",
        )
        result = _classify_failure(record)
        # "missing" (dependency) + "import" (dependency) + "timeout" (timeout)
        # But "timeout" appears twice and "module" appears too
        assert result == "dependency", (
            f"Expected dependency (highest score), got {result}"
        )


class TestGenerateAntibody:
    """Unit tests for _generate_antibody."""

    def test_known_category_uses_template(self):
        record = _make_record(agent_role="embedded-firmware-engineer")
        antibody = _generate_antibody("config_miss", record)
        assert "config_miss" not in antibody  # Should NOT contain the category name
        assert "config" in antibody or "configuration" in antibody
        assert "embedded-firmware-engineer" in antibody  # Context included

    def test_unknown_category_uses_generic_fallback(self):
        record = _make_record(agent_role="test-agent")
        antibody = _generate_antibody("nonexistent_category", record)
        assert "Investigate" in antibody
        assert "monitoring" in antibody

    def test_vaccine_template_exists_for_each_category(self):
        """Every failure category should have a vaccine template."""
        for category in FAILURE_CATEGORIES:
            vaccine = _generate_vaccine(category)
            assert vaccine and len(vaccine) > 10, (
                f"Missing vaccine template for {category}"
            )

    def test_antibody_template_exists_for_each_category(self):
        """Every failure category should have an antibody template."""
        for category in FAILURE_CATEGORIES:
            record = _make_record()
            antibody = _generate_antibody(category, record)
            assert antibody and len(antibody) > 10, (
                f"Missing or empty antibody template for {category}"
            )


class TestAllCategoriesConfigured:
    """Ensure all eight failure categories are fully defined."""

    def test_category_order_coverage(self):
        """Every category in FAILURE_CATEGORIES should appear in CATEGORY_ORDER."""
        from ai_embedded_company.evolution.classifier import CATEGORY_ORDER

        assert set(CATEGORY_ORDER) == set(FAILURE_CATEGORIES.keys()), (
            "CATEGORY_ORDER must cover all FAILURE_CATEGORIES"
        )

    def test_all_categories_have_keywords(self):
        for cat, config in FAILURE_CATEGORIES.items():
            assert config.get("keywords"), f"Category {cat} has no keywords"
            assert config.get("description"), f"Category {cat} has no description"
            assert config.get("severity"), f"Category {cat} has no severity"

    def test_all_categories_have_templates(self):
        for cat in FAILURE_CATEGORIES:
            assert cat in ANTIBODY_TEMPLATES, f"Missing antibody for {cat}"
            assert cat in VACCINE_TEMPLATES, f"Missing vaccine for {cat}"
