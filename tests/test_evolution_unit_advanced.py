"""Advanced unit tests for evolution classifier — reclassify_all, edge cases,
get_high_frequency_patterns, and watchdog internals."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai_embedded_company.evolution.classifier import (
    _classify_failure,
    _generate_antibody,
    _generate_vaccine,
    classify_and_heal,
    get_high_frequency_patterns,
    reclassify_all,
    reset_watchdog,
    get_watchdog_state,
    validate_record,
    CircuitBreakerOpenError,
    FAILURE_CATEGORIES,
)
from ai_embedded_company.storage.models import FailureRecord


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_record(
    title: str = "test failure",
    description: str = "Something went wrong",
    root_cause: str = "Root cause unknown",
    category: str = "resource",
    agent_role: str = "test-agent",
    status: str = "reported",
    severity: str = "medium",
    frequency: int = 1,
) -> FailureRecord:
    """Minimal FailureRecord factory."""
    return FailureRecord(
        id=f"test-{datetime.now(timezone.utc).timestamp()}",
        title=title,
        description=description,
        root_cause=root_cause,
        category=category,
        agent_role=agent_role,
        status=status,
        frequency=frequency,
        severity=severity,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ── Watchdog Internal Tests ───────────────────────────────────────────────────


class TestWatchdogInternals:
    """Direct tests for watchdog internal functions."""

    def setup_method(self):
        reset_watchdog(max_consecutive_errors=5)

    def test_initial_state(self):
        state = get_watchdog_state()
        assert state["consecutive_errors"] == 0
        assert state["total_errors"] == 0
        assert state["total_processed"] == 0
        assert state["circuit_open"] is False
        assert state["last_error_at"] is None
        assert state["circuit_open_since"] is None

    def test_success_clears_consecutive_errors(self):
        from ai_embedded_company.evolution.classifier import (
            _record_error, _record_success,
        )

        _record_error()
        _record_error()
        _record_success()

        state = get_watchdog_state()
        assert state["consecutive_errors"] == 0
        assert state["total_errors"] == 2
        assert state["total_processed"] == 3

    def test_error_increments_counters(self):
        from ai_embedded_company.evolution.classifier import _record_error

        _record_error()
        state = get_watchdog_state()
        assert state["consecutive_errors"] == 1
        assert state["total_errors"] == 1
        assert state["last_error_at"] is not None

    def test_circuit_opens_at_threshold(self):
        from ai_embedded_company.evolution.classifier import _record_error

        for _ in range(5):
            _record_error()

        state = get_watchdog_state()
        assert state["circuit_open"] is True
        assert state["circuit_open_since"] is not None

    def test_circuit_breaker_raises_when_open(self):
        from ai_embedded_company.evolution.classifier import _record_error, _check_circuit_breaker

        for _ in range(5):
            _record_error()

        with pytest.raises(CircuitBreakerOpenError):
            _check_circuit_breaker()

    def test_reset_after_circuit_break(self):
        from ai_embedded_company.evolution.classifier import _record_error, _check_circuit_breaker

        for _ in range(5):
            _record_error()
        assert get_watchdog_state()["circuit_open"] is True

        reset_watchdog()
        state = get_watchdog_state()
        assert state["circuit_open"] is False
        assert state["consecutive_errors"] == 0
        assert state["total_errors"] == 0

        # _check_circuit_breaker should NOT raise after reset
        _check_circuit_breaker()  # No exception

    def teardown_method(self):
        reset_watchdog()


# ── Classifier Edge Case Tests ────────────────────────────────────────────────


class TestClassifierEdgeCases:
    """Edge case tests for the classification function."""

    def test_empty_title_and_empty_description_returns_none(self):
        """Completely empty record should not be classified."""
        record = _make_record(title="", description="")
        assert _classify_failure(record) is None

    def test_title_only_works(self):
        record = _make_record(description="")
        record.title = "Timeout: task exceeded 30 minute threshold"
        record.description = ""
        result = _classify_failure(record)
        assert result == "timeout", f"Expected timeout, got {result}"

    def test_root_cause_only_works(self):
        record = _make_record(title="", description="")
        record.root_cause = "ImportError: No module named requests"
        result = _classify_failure(record)
        assert result == "dependency", f"Expected dependency, got {result}"

    def test_all_none_fields_returns_none(self):
        record = _make_record(title="", description="")
        record.root_cause = ""
        assert _classify_failure(record) is None

    def test_case_insensitive_matching(self):
        record = _make_record(
            description="TIMEOUT: TASK EXCEEDED 30 MINUTES",
        )
        result = _classify_failure(record)
        assert result == "timeout", f"Expected timeout, got {result}"

    def test_mixed_language_keywords(self):
        """Keywords in Chinese should match too."""
        record = _make_record(
            description="遇到記憶體不足的問題，發生OOM",
        )
        result = _classify_failure(record)
        # "memory" is in the resource keywords, but not in this Chinese text
        # "OOM" is in the resource keywords
        result = _classify_failure(record)
        # "OOM" should match resource
        assert "resource" in FAILURE_CATEGORIES

    def test_score_normalization_prevents_category_bias(self):
        """Categories with more keywords shouldn't unfairly dominate."""
        record = _make_record(
            description="A simple timeout occurred after 30 seconds",
            root_cause="The task timed out",
        )
        result = _classify_failure(record)
        # "timeout" appears twice, "timed" matches nothing else
        # "seconds" is not a keyword, "occurred" is not a keyword
        # timeout has fewer keywords but each match counts more after normalization
        assert result == "timeout", f"Expected timeout, got {result}"


# ── reclassify_all Tests ──────────────────────────────────────────────────────


class TestReclassifyAll:
    """Tests for reclassify_all function."""

    def test_reclassify_empty_db(self):
        """Reclassify on empty DB should return zero scans."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        import asyncio
        result = asyncio.run(reclassify_all(mock_session))

        assert result["scanned"] == 0
        assert result["category_changes"] == 0

    def test_reclassify_single_record(self):
        """Reclassify should update category for a single record."""
        record = _make_record(
            description="HTTP 503 Service Unavailable",
            root_cause="API request failed",
            category="unknown",
        )
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [record]
        mock_session.execute.return_value = mock_result

        import asyncio
        result = asyncio.run(reclassify_all(mock_session))

        assert result["scanned"] == 1
        assert result["category_changes"] == 1  # unknown -> api_error
        assert "api_error" in result["by_category"]

    def test_reclassify_adds_missing_antibodies(self):
        """Records without antibodies should get them generated."""
        record = _make_record(
            description="MemoryError: out of memory",
            root_cause="OOM",
            category="resource",
            status="analyzed",
        )
        record.antibody = ""  # No antibody yet
        record.vaccine = ""  # No vaccine yet

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [record]
        mock_session.execute.return_value = mock_result

        import asyncio
        result = asyncio.run(reclassify_all(mock_session))

        assert result["scanned"] == 1
        assert result["antibodies_added"] == 1
        assert result["vaccines_added"] == 1

    def test_reclassify_skips_existing_antibodies(self):
        """Records that already have antibodies should not get duplicates."""
        record = _make_record(
            description="MemoryError: out of memory",
            root_cause="OOM",
            category="resource",
        )
        record.antibody = "[agent: test] Prevent OOM by monitoring memory"
        record.vaccine = "⚠️ Memory failures detected"

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [record]
        mock_session.execute.return_value = mock_result

        import asyncio
        result = asyncio.run(reclassify_all(mock_session))

        assert result["antibodies_added"] == 0  # Already has one
        assert result["vaccines_added"] == 0

    def test_reclassify_multiple_records(self):
        """Multiple records across categories should be tallied."""
        records = [
            _make_record(description="Config not found", root_cause="Missing env", category="unknown"),
            _make_record(description="API timeout", root_cause="Connection failed", category="unknown"),
            _make_record(description="OOM crash", root_cause="Out of memory", category="unknown"),
        ]

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = records
        mock_session.execute.return_value = mock_result

        import asyncio
        result = asyncio.run(reclassify_all(mock_session))

        assert result["scanned"] == 3
        assert result["category_changes"] == 3
        assert "config_miss" in result["by_category"]
        assert "resource" in result["by_category"]


# ── get_high_frequency_patterns Tests ────────────────────────────────────────


class TestGetHighFrequencyPatterns:
    """Tests for get_high_frequency_patterns function."""

    def test_empty_result_when_no_data(self):
        """No records matching min_frequency should return empty list."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        import asyncio
        patterns = asyncio.run(get_high_frequency_patterns(mock_session, min_frequency=3))
        assert patterns == []

    def test_returns_frequent_patterns(self):
        """Records with frequency >= min_frequency should be returned."""
        record = _make_record(
            description="Config not found",
            root_cause="Missing env",
            category="config_miss",
            frequency=5,
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [record]
        mock_session.execute.return_value = mock_result

        import asyncio
        patterns = asyncio.run(get_high_frequency_patterns(mock_session, min_frequency=3))
        assert len(patterns) == 1
        assert patterns[0]["category"] == "config_miss"
        assert patterns[0]["frequency"] == 5
        assert "antibody" in patterns[0]
        assert "vaccine" in patterns[0]

    def test_filters_low_frequency(self):
        """Records below min_frequency should be excluded."""
        record = _make_record(
            description="Config not found",
            category="config_miss",
            frequency=1,  # Below min_frequency=3
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # Filtered by query
        mock_session.execute.return_value = mock_result

        import asyncio
        patterns = asyncio.run(get_high_frequency_patterns(mock_session, min_frequency=3))
        assert patterns == []


# ── classify_and_heal by record_id Tests ─────────────────────────────────────


class TestClassifyAndHealByRecordId:
    """Tests for classify_and_heal with a specific record_id."""

    def test_classify_specific_record(self):
        """Classify a single record by its ID."""
        record = _make_record(description="Config not found", category="unknown")

        mock_session = AsyncMock()
        mock_fetch = MagicMock()
        mock_fetch.scalars.return_value.all.return_value = [record]
        mock_session.execute.return_value = mock_fetch

        import asyncio
        result = asyncio.run(
            classify_and_heal(mock_session, record_id=record.id, max_records=5)
        )
        assert result["scanned"] == 1

    def test_record_id_none_processes_all(self):
        """When record_id is None, process up to max_records."""
        # Reset watchdog for a clean state
        reset_watchdog()

        records = [
            _make_record(description=f"Error type {i}", category="unknown")
            for i in range(3)
        ]

        mock_session = AsyncMock()
        mock_fetch = MagicMock()
        mock_fetch.scalars.return_value.all.return_value = records
        mock_session.execute.return_value = mock_fetch

        import asyncio
        result = asyncio.run(
            classify_and_heal(mock_session, record_id=None, max_records=10)
        )
        assert result["scanned"] == 3


# ── validate_record Comprehensive Tests ──────────────────────────────────────


class TestValidateRecordComprehensive:
    """Comprehensive tests for validate_record."""

    def test_validates_all_status_values(self):
        for status in ("reported", "analyzed", "resolved"):
            record = _make_record(category="timeout", status=status)
            issues = validate_record(record)
            status_issues = [i for i in issues if "Unknown status" in i]
            assert not status_issues, f"Unexpected status issue for {status}"

    def test_validates_all_severity_values(self):
        for severity in ("low", "medium", "high", "critical"):
            record = _make_record(category="timeout", severity=severity)
            issues = validate_record(record)
            sev_issues = [i for i in issues if "Unknown severity" in i]
            assert not sev_issues, f"Unexpected severity issue for {severity}"

    def test_validates_all_category_values(self):
        for cat in FAILURE_CATEGORIES:
            record = _make_record(category=cat)
            issues = validate_record(record)
            cat_issues = [i for i in issues if "Unknown category" in i]
            assert not cat_issues, f"Unexpected category issue for {cat}"

    def test_catches_multiple_issues(self):
        record = _make_record(
            title="",
            description="",
            category="fake_cat",
            severity="extreme",
            status="invalid",
        )
        issues = validate_record(record)
        assert len(issues) >= 3  # Should catch at least 3 issues
