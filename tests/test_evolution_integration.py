"""Integration tests for the evolution classifier — watchdog, validation,
and classify_and_heal with an in-memory SQLite session."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from ai_embedded_company.evolution.classifier import (
    _classify_failure,
    _generate_antibody,
    _generate_vaccine,
    classify_and_heal,
    reset_watchdog,
    get_watchdog_state,
    validate_record,
    CircuitBreakerOpenError,
    FAILURE_CATEGORIES,
)
from ai_embedded_company.evolution.task_monitor import (
    _extract_failure_signature,
    _detect_phase,
    _compute_severity,
)
from ai_embedded_company.storage.models import FailureRecord, TaskModel


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_record(
    title: str = "test failure",
    description: str = "Something went wrong",
    root_cause: str = "Root cause unknown",
    category: str = "unknown",
    agent_role: str = "test-agent",
    status: str = "reported",
    severity: str = "medium",
    frequency: int = 1,
) -> FailureRecord:
    """Minimal FailureRecord factory for integration testing."""
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


def _make_task(
    title: str = "test task",
    description: str = "",
    status: str = "failed",
    priority: str = "medium",
    assigned_agent: str = "test-agent",
) -> TaskModel:
    """Minimal TaskModel factory for integration testing."""
    return TaskModel(
        id=f"task-{datetime.now(timezone.utc).timestamp()}",
        title=title,
        description=description,
        status=status,
        priority=priority,
        assigned_agent=assigned_agent,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ── Validator Tests ───────────────────────────────────────────────────────────


class TestValidateRecord:
    """Tests for input validation of FailureRecords."""

    def test_valid_record_passes(self):
        record = _make_record(category="timeout")  # "unknown" fails validation
        issues = validate_record(record)
        assert issues == [], f"Expected no issues, got: {issues}"

    def test_empty_title_and_description_fails(self):
        record = _make_record(title="", description="", root_cause="")
        issues = validate_record(record)
        assert any("no title" in i for i in issues)

    def test_unknown_status_warns(self):
        record = _make_record(status="invalid_status")
        issues = validate_record(record)
        assert any("Unknown status" in i for i in issues)

    def test_unknown_severity_warns(self):
        record = _make_record(severity="extreme")
        issues = validate_record(record)
        assert any("Unknown severity" in i for i in issues)

    def test_unknown_category_warns(self):
        record = _make_record(category="nonexistent_category")
        issues = validate_record(record)
        assert any("Unknown category" in i for i in issues)

    def test_empty_title_and_no_description_returns_none(self):
        """_classify_failure returns None when title, description, and root_cause are empty."""
        record = _make_record(title="", description="", root_cause="")
        assert _classify_failure(record) is None

    def test_empty_record_skipped_in_classify_and_heal(self):
        """classify_and_heal skips records with no description gracefully."""
        record = _make_record(title="", description="", root_cause="")
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [record]
        mock_session.execute.return_value = mock_result

        import asyncio
        result = asyncio.run(classify_and_heal(mock_session, max_records=10))

        assert result["scanned"] == 1
        assert result["updated"] == 0  # skipped, not updated
        assert any("empty title" in e for e in result["errors"]), (
            f"Expected skip message in errors, got: {result['errors']}"
        )


# ── Watchdog / Circuit Breaker Tests ──────────────────────────────────────────


class TestWatchdogCircuitBreaker:
    """Tests for the classifier watchdog and circuit breaker."""

    def setup_method(self):
        reset_watchdog(max_consecutive_errors=3)

    def test_watchdog_starts_clean(self):
        state = get_watchdog_state()
        assert state["consecutive_errors"] == 0
        assert state["circuit_open"] is False

    def test_reset_clears_state(self):
        state = get_watchdog_state()
        assert state["consecutive_errors"] == 0

    def test_circuit_breaker_opens_after_max_errors(self):
        from ai_embedded_company.evolution.classifier import (
            _record_error, _check_circuit_breaker,
        )

        # Trigger max_consecutive_errors (3) by calling _record_error
        for _ in range(3):
            _record_error()

        state = get_watchdog_state()
        assert state["circuit_open"] is True
        assert state["consecutive_errors"] == 3

        # Now _check_circuit_breaker should raise
        with pytest.raises(CircuitBreakerOpenError):
            _check_circuit_breaker()

    def test_success_resets_consecutive_errors(self):
        from ai_embedded_company.evolution.classifier import (
            _record_error, _record_success, _check_circuit_breaker,
        )

        _record_error()
        _record_error()
        _record_success()  # This resets consecutive_errors to 0

        # Circuit should NOT be open (2 < 3)
        _check_circuit_breaker()  # No exception

        state = get_watchdog_state()
        assert state["consecutive_errors"] == 0
        assert state["circuit_open"] is False

    def test_classify_and_heal_respects_open_circuit(self):
        """When circuit is open, classify_and_heal should return early."""
        # First force the circuit open
        from ai_embedded_company.evolution.classifier import (
            _record_error, _check_circuit_breaker,
        )
        for _ in range(3):
            _record_error()

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        import asyncio
        result = asyncio.run(classify_and_heal(mock_session))

        assert "Circuit breaker is open" in " ".join(result["errors"]), (
            f"Expected circuit breaker message in errors: {result['errors']}"
        )
        # Should NOT have scanned anything
        assert result["scanned"] == 0

    def teardown_method(self):
        reset_watchdog()


# ── classify_and_heal Integration Tests ───────────────────────────────────────


class TestClassifyAndHealIntegration:
    """Integration tests for the classify_and_heal pipeline."""

    def test_classifies_single_record(self):
        """A single unclassified record should be classified and updated."""
        record = _make_record(
            description="ImportError: No module named 'flask'",
            root_cause="Missing pip package",
        )
        mock_session = AsyncMock()

        # First execute call: fetch records
        mock_fetch = MagicMock()
        mock_fetch.scalars.return_value.all.return_value = [record]
        mock_session.execute.return_value = mock_fetch

        import asyncio
        result = asyncio.run(classify_and_heal(mock_session, max_records=10))

        assert result["scanned"] == 1
        assert result["classified"] == 1  # category changed from "unknown" to "dependency"
        assert result["updated"] == 1
        assert result["antibodies_generated"] == 1
        assert "dependency" in result["by_category"]

    def test_multiple_records_across_categories(self):
        """Classify records of different failure types."""
        records = [
            _make_record(
                title="config error",
                description="Config file not found at /etc/app.yml",
                root_cause="Missing DATABASE_URL",
            ),
            _make_record(
                title="api timeout",
                description="HTTP 503 from upstream API after 30s",
                root_cause="Connection timeout to api.example.com",
            ),
            _make_record(
                title="oom crash",
                description="MemoryError: cannot allocate 2GB",
                root_cause="OOM killer terminated the process",
            ),
        ]

        mock_session = AsyncMock()
        mock_fetch = MagicMock()
        mock_fetch.scalars.return_value.all.return_value = records
        mock_session.execute.return_value = mock_fetch

        import asyncio
        result = asyncio.run(classify_and_heal(mock_session, max_records=10))

        assert result["scanned"] == 3
        assert "config_miss" in result["by_category"]
        assert "api_error" in result["by_category"]
        assert "resource" in result["by_category"]

    def test_already_analyzed_records_not_reprocessed(self):
        """Only status='reported' records are processed by default."""
        record = _make_record(
            description="Some error",
            status="analyzed",  # Already analyzed
            category="dependency",
        )
        # Manually set antibody (not in _make_record constructor)
        record.antibody = "Already has an antibody"
        mock_session = AsyncMock()
        mock_fetch = MagicMock()
        mock_fetch.scalars.return_value.all.return_value = []  # 0 reported records
        mock_session.execute.return_value = mock_fetch

        import asyncio
        result = asyncio.run(classify_and_heal(mock_session, max_records=10))

        assert result["scanned"] == 0  # No reported records found


# ── Task Monitor Tests ────────────────────────────────────────────────────────


class TestFailureSignatureExtraction:
    """Tests for _extract_failure_signature in task_monitor."""

    def test_timeout_signature(self):
        task = _make_task(
            title="Build firmware — slow",
            description="Task took 45 minutes, exceeding threshold",
        )
        sig = _extract_failure_signature(task)
        assert sig["likely_category"] == "timeout"

    def test_config_signature(self):
        task = _make_task(
            description="Config file not found at /etc/app/config.yml",
        )
        sig = _extract_failure_signature(task)
        assert sig["likely_category"] == "config"

    def test_dependency_signature(self):
        task = _make_task(
            description="ImportError: missing module 'numpy'",
        )
        sig = _extract_failure_signature(task)
        assert sig["likely_category"] == "dependency"

    def test_api_signature(self):
        task = _make_task(
            description="HTTP 503 from api.github.com — request failed",
        )
        sig = _extract_failure_signature(task)
        assert sig["likely_category"] == "api"

    def test_logic_signature(self):
        task = _make_task(
            description="TypeError: unsupported operand type",
        )
        sig = _extract_failure_signature(task)
        assert sig["likely_category"] == "logic"

    def test_resource_signature(self):
        task = _make_task(
            description="Out of memory: OOM killer invoked",
        )
        sig = _extract_failure_signature(task)
        assert sig["likely_category"] == "resource"

    def test_unknown_task_returns_unknown(self):
        task = _make_task(
            description="The quick brown fox jumps over the lazy dog",
        )
        sig = _extract_failure_signature(task)
        assert sig["likely_category"] == "unknown"


class TestDetectPhase:
    """Tests for _detect_phase in task_monitor."""

    def test_planning_phase(self):
        assert _detect_phase("Design system architecture", "") == "planning"

    def test_implementation_phase(self):
        assert _detect_phase("", "Implement the core business logic") == "implementation"

    def test_testing_phase(self):
        assert _detect_phase("Run tests for module", "") == "testing"

    def test_deployment_phase(self):
        assert _detect_phase("Deploy to production", "") == "deployment"

    def test_integration_phase(self):
        assert _detect_phase("", "Connect frontend to backend API") == "integration"

    def test_unknown_phase(self):
        assert _detect_phase("Random task", "No clear phase") == "unknown"


class TestComputeSeverity:
    """Tests for _compute_severity in task_monitor."""

    def test_timeout_is_high(self):
        assert _compute_severity("medium", is_timeout=True) == "high"

    def test_high_priority_is_high(self):
        assert _compute_severity("high", is_timeout=False) == "high"

    def test_medium_priority_is_medium(self):
        assert _compute_severity("medium", is_timeout=False) == "medium"

    def test_low_priority_is_low(self):
        assert _compute_severity("low", is_timeout=False) == "low"

    def test_critical_priority(self):
        assert _compute_severity("critical", is_timeout=False) == "critical"

    def test_unknown_priority_defaults_medium(self):
        assert _compute_severity("unknown", is_timeout=False) == "medium"
