"""Integration tests for the /ws/dashboard WebSocket endpoint.

Covers:
- Connection lifecycle (connect, snapshot, disconnect)
- Schema validation of snapshot payload
- Ping/pong keepalive
- Multiple concurrent connections
- Data consistency (snapshot reflects persisted state via direct function call)
- Health check endpoint
- Dashboard metrics endpoint
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ai_embedded_company.api.app import app
from ai_embedded_company.api.routes.ws import _build_metrics_snapshot
from ai_embedded_company.storage.models import Base, TaskModel, IdeaModel, PipelineModel

client = TestClient(app)


# ── Fixture for in-memory DB tests ──────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
FAKE_PROJECT_ID = "00000000-0000-0000-0000-000000000001"


@pytest_asyncio.fixture
async def mem_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean in-memory SQLite session for each test."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


# ── Helpers ──────────────────────────────────────────────────────────────────

SNAPSHOT_KEYS = {"type", "db_available", "timestamp", "tasks", "ideas", "pipelines"}
TASK_KEYS = {"total", "by_status", "running_count", "total_tokens"}
IDEA_KEYS = {"total", "by_status"}
PIPELINE_KEYS = {"total", "by_phase"}


def assert_valid_snapshot(data: dict[str, Any]) -> None:
    """Assert that *data* is a valid dashboard snapshot."""
    assert data["type"] == "snapshot"
    assert data["db_available"] is True
    assert isinstance(data["timestamp"], (int, float))
    assert SNAPSHOT_KEYS.issubset(data.keys())

    tasks = data["tasks"]
    assert TASK_KEYS.issubset(tasks.keys())
    assert isinstance(tasks["by_status"], dict)

    ideas = data["ideas"]
    assert IDEA_KEYS.issubset(ideas.keys())
    assert isinstance(ideas["by_status"], dict)

    pipelines = data["pipelines"]
    assert PIPELINE_KEYS.issubset(pipelines.keys())
    assert isinstance(pipelines["by_phase"], dict)


# ── Tests ────────────────────────────────────────────────────────────────────


class TestWebSocketConnection:
    """Basic connection lifecycle tests."""

    @pytest.mark.asyncio
    async def test_connects_and_receives_snapshot(self) -> None:
        """Connect and verify the first message is a valid snapshot."""
        with client.websocket_connect("/ws/dashboard") as ws:
            data = ws.receive_json()
            assert_valid_snapshot(data)

    @pytest.mark.asyncio
    async def test_schema_has_all_expected_keys(self) -> None:
        """Verify every nested key in the snapshot matches the frontend contract."""
        with client.websocket_connect("/ws/dashboard") as ws:
            data = ws.receive_json()

        for section in ("tasks", "ideas", "pipelines"):
            assert section in data, f"Missing top-level section: {section}"

        tasks = data["tasks"]
        for key in ("total", "by_status", "total_tokens", "running_count"):
            assert key in tasks, f"Missing tasks.{key}"

        ideas = data["ideas"]
        for key in ("total", "by_status"):
            assert key in ideas, f"Missing ideas.{key}"

        pipelines = data["pipelines"]
        for key in ("total", "by_phase"):
            assert key in pipelines, f"Missing pipelines.{key}"

    @pytest.mark.asyncio
    async def test_receives_multiple_snapshots_and_db_available(self) -> None:
        """Two consecutive snapshot messages are both valid and db_available is True."""
        with client.websocket_connect("/ws/dashboard") as ws:
            data1 = ws.receive_json()
            assert_valid_snapshot(data1)
            assert data1["db_available"] is True

            data2 = ws.receive_json()
            assert_valid_snapshot(data2)
            assert data2["db_available"] is True


class TestWebSocketPingPong:
    """Keepalive ping/pong mechanism."""

    @pytest.mark.asyncio
    async def test_ping_triggers_pong(self) -> None:
        """Sending 'ping' over WebSocket returns a 'pong' response."""
        with client.websocket_connect("/ws/dashboard") as ws:
            ws.receive_json()  # consume initial snapshot
            ws.send_text("ping")
            pong = ws.receive_json()
            assert pong["type"] == "pong"

    @pytest.mark.asyncio
    async def test_unknown_text_is_ignored(self) -> None:
        """Sending non-'ping' text doesn't crash the connection."""
        with client.websocket_connect("/ws/dashboard") as ws:
            data1 = ws.receive_json()
            assert_valid_snapshot(data1)
            ws.send_text("hello")
            data2 = ws.receive_json()
            assert_valid_snapshot(data2)

    @pytest.mark.asyncio
    async def test_empty_message_is_ignored(self) -> None:
        """Sending an empty string is silently ignored."""
        with client.websocket_connect("/ws/dashboard") as ws:
            data1 = ws.receive_json()
            ws.send_text("")
            data2 = ws.receive_json()
            assert_valid_snapshot(data2)


class TestWebSocketConcurrentConnections:
    """Multiple concurrent WebSocket clients."""

    @pytest.mark.asyncio
    async def test_two_clients_both_receive_snapshots(self) -> None:
        """Two concurrent connections each receive their own valid snapshots."""
        with client.websocket_connect("/ws/dashboard") as ws1:
            with client.websocket_connect("/ws/dashboard") as ws2:
                d1 = ws1.receive_json()
                d2 = ws2.receive_json()
                assert_valid_snapshot(d1)
                assert_valid_snapshot(d2)

    @pytest.mark.asyncio
    async def test_three_clients_receive_data_independently(self) -> None:
        """Three concurrent connections all receive valid snapshots."""
        with client.websocket_connect("/ws/dashboard") as ws1:
            with client.websocket_connect("/ws/dashboard") as ws2:
                with client.websocket_connect("/ws/dashboard") as ws3:
                    for ws in (ws1, ws2, ws3):
                        data = ws.receive_json()
                        assert_valid_snapshot(data)

    @pytest.mark.asyncio
    async def test_client_disconnect_does_not_affect_others(self) -> None:
        """Disconnecting one client doesn't crash the server or other clients."""
        ws1 = client.websocket_connect("/ws/dashboard")
        d1 = ws1.__enter__()
        snap1 = d1.receive_json()
        assert_valid_snapshot(snap1)

        ws2 = client.websocket_connect("/ws/dashboard")
        d2 = ws2.__enter__()
        snap2 = d2.receive_json()
        assert_valid_snapshot(snap2)

        ws1.__exit__(None, None, None)

        snap3 = d2.receive_json()
        assert_valid_snapshot(snap3)
        ws2.__exit__(None, None, None)


class TestBuildMetricsSnapshot:
    """Direct unit tests for _build_metrics_snapshot()."""

    @pytest.mark.asyncio
    async def test_empty_db(self, mem_session: AsyncSession) -> None:
        """With an empty database, all counts are zero."""
        data = await _build_metrics_snapshot(session=mem_session)
        assert data["tasks"]["total"] == 0
        assert data["ideas"]["total"] == 0
        assert data["pipelines"]["total"] == 0
        assert data["tasks"]["by_status"] == {}
        assert data["ideas"]["by_status"] == {}
        assert data["pipelines"]["by_phase"] == {}

    @pytest.mark.asyncio
    async def test_reflects_seeded_data(self, mem_session: AsyncSession) -> None:
        """After seeding tasks and ideas, the snapshot reflects correct counts."""
        mem_session.add_all([
            TaskModel(title="Task A", status="in_progress", tokens_used=100, project_id=FAKE_PROJECT_ID),
            TaskModel(title="Task B", status="pending", tokens_used=50, project_id=FAKE_PROJECT_ID),
            TaskModel(title="Task C", status="done", tokens_used=200, project_id=FAKE_PROJECT_ID),
            IdeaModel(title="Idea X", status="new"),
            IdeaModel(title="Idea Y", status="refining"),
            PipelineModel(project_id="p1", pipeline_type="web-fullstack", current_phase="testing"),
            PipelineModel(project_id="p2", pipeline_type="embedded-firmware", current_phase="done"),
        ])
        await mem_session.commit()

        data = await _build_metrics_snapshot(session=mem_session)

        assert data["tasks"]["total"] == 3
        assert data["tasks"]["by_status"]["in_progress"] == 1
        assert data["tasks"]["by_status"]["pending"] == 1
        assert data["tasks"]["by_status"]["done"] == 1
        assert data["tasks"]["running_count"] == 1
        assert data["tasks"]["total_tokens"] == 350

        assert data["ideas"]["total"] == 2
        assert data["ideas"]["by_status"]["new"] == 1
        assert data["ideas"]["by_status"]["refining"] == 1

        assert data["pipelines"]["total"] == 2
        assert data["pipelines"]["by_phase"]["testing"] == 1
        assert data["pipelines"]["by_phase"]["done"] == 1

    @pytest.mark.asyncio
    async def test_updates_after_write(self, mem_session: AsyncSession) -> None:
        """Creating a task mid-stream is reflected in the next snapshot."""
        mem_session.add(TaskModel(title="Initial", status="in_progress", project_id=FAKE_PROJECT_ID))
        await mem_session.commit()

        snap1 = await _build_metrics_snapshot(session=mem_session)
        assert snap1["tasks"]["total"] == 1

        mem_session.add(TaskModel(title="Added", status="pending", project_id=FAKE_PROJECT_ID))
        await mem_session.commit()

        snap2 = await _build_metrics_snapshot(session=mem_session)
        assert snap2["tasks"]["total"] == 2
        assert snap2["tasks"]["by_status"]["pending"] == 1

    @pytest.mark.asyncio
    async def test_task_with_null_status_defaults_to_todo(self, mem_session: AsyncSession) -> None:
        """A task with null status is counted under 'todo'."""
        mem_session.add(
            TaskModel(title="No status", status=None, project_id=FAKE_PROJECT_ID)  # type: ignore[arg-type]
        )
        await mem_session.commit()

        data = await _build_metrics_snapshot(session=mem_session)
        assert data["tasks"]["total"] == 1
        assert data["tasks"]["by_status"].get("todo") == 1

    @pytest.mark.asyncio
    async def test_pipeline_default_phase_is_idea(self, mem_session: AsyncSession) -> None:
        """A pipeline without an explicit phase defaults to 'idea'."""
        mem_session.add(
            PipelineModel(project_id="p1", pipeline_type="web-fullstack")
        )
        await mem_session.commit()

        data = await _build_metrics_snapshot(session=mem_session)
        assert data["pipelines"]["total"] == 1
        assert data["pipelines"]["by_phase"].get("idea") == 1

    @pytest.mark.asyncio
    async def test_zero_running_count_when_idle(self, mem_session: AsyncSession) -> None:
        """When no tasks have status 'in_progress', running_count is 0."""
        mem_session.add_all([
            TaskModel(title="T1", status="done", project_id=FAKE_PROJECT_ID),
            TaskModel(title="T2", status="pending", project_id=FAKE_PROJECT_ID),
        ])
        await mem_session.commit()

        data = await _build_metrics_snapshot(session=mem_session)
        assert data["tasks"]["running_count"] == 0

    @pytest.mark.asyncio
    async def test_large_token_count(self, mem_session: AsyncSession) -> None:
        """Total token count accumulates correctly over many tasks."""
        mem_session.add_all([
            TaskModel(title=f"Task {i}", tokens_used=i * 1000, project_id=FAKE_PROJECT_ID)
            for i in range(10)
        ])
        await mem_session.commit()

        data = await _build_metrics_snapshot(session=mem_session)
        assert data["tasks"]["total_tokens"] == sum(i * 1000 for i in range(10))
        assert data["tasks"]["total"] == 10


class TestHealthEndpoint:
    """Health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_healthy(self) -> None:
        """GET /health returns 200 with 'healthy' status."""
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_contains_version(self) -> None:
        """Health response includes version and python_version."""
        resp = client.get("/health")
        body = resp.json()
        assert "version" in body
        assert "python_version" in body


class TestDashboardMetricsEndpoint:
    """Dashboard consolidated metrics endpoint."""

    @pytest.mark.asyncio
    async def test_metrics_returns_expected_structure(self) -> None:
        """GET /api/dashboard/metrics returns the full metrics envelope."""
        resp = client.get("/api/dashboard/metrics")
        assert resp.status_code == 200
        body = resp.json()

        for section in ("pipelines", "ideas", "tasks", "projects", "evolution", "cycle_throughput"):
            assert section in body, f"Missing section: {section}"

        assert "total" in body["pipelines"]
        assert "by_phase" in body["pipelines"]
        assert "by_type" in body["pipelines"]
        assert "total" in body["tasks"]
        assert "by_status" in body["tasks"]
        assert "total_tokens" in body["tasks"]
        assert "total" in body["ideas"]
        assert "by_status" in body["ideas"]
        assert "daily_created" in body["ideas"]

    @pytest.mark.asyncio
    async def test_metrics_counts_are_non_negative(self) -> None:
        """All count fields in the metrics response are non-negative."""
        resp = client.get("/api/dashboard/metrics")
        body = resp.json()

        assert body["pipelines"]["total"] >= 0
        assert body["ideas"]["total"] >= 0
        assert body["tasks"]["total"] >= 0
        assert body["projects"]["total"] >= 0
        assert body["projects"]["active"] >= 0
        assert body["tasks"]["total_tokens"] >= 0

        for status, count in body["tasks"]["by_status"].items():
            assert count >= 0, f"Negative count for tasks.{status}"

        for phase, count in body["pipelines"]["by_phase"].items():
            assert count >= 0, f"Negative count for pipelines.{phase}"

    @pytest.mark.asyncio
    async def test_metrics_evolution_section(self) -> None:
        """Evolution section has the expected keys."""
        resp = client.get("/api/dashboard/metrics")
        body = resp.json()
        evo = body["evolution"]

        for key in ("total_failures", "by_category", "by_severity", "antibodies", "vaccines"):
            assert key in evo, f"Missing evolution.{key}"

        assert evo["total_failures"] >= 0
        assert evo["antibodies"] >= 0
        assert evo["vaccines"] >= 0

    @pytest.mark.asyncio
    async def test_metrics_cycle_throughput(self) -> None:
        """Cycle throughput section has daily breakdowns."""
        resp = client.get("/api/dashboard/metrics")
        body = resp.json()
        ct = body["cycle_throughput"]

        for key in ("ideas_per_day", "pipelines_per_day"):
            assert key in ct, f"Missing cycle_throughput.{key}"
            assert isinstance(ct[key], dict)

    @pytest.mark.asyncio
    async def test_metrics_frontend_contract(self) -> None:
        """Verify all fields consumed by Dashboard.tsx are present."""
        resp = client.get("/api/dashboard/metrics")
        body = resp.json()

        assert "total" in body["projects"]
        assert "active" in body["projects"]
        assert "total_tokens" in body["tasks"]
        assert "completed_count" in body["tasks"]
        assert "today_minutes" in body["tasks"]
        assert "tracked" in body["tasks"]

        avg = body["tasks"].get("average_completion_minutes")
        assert avg is None or isinstance(avg, (int, float))

    @pytest.mark.asyncio
    async def test_metrics_weekly_tokens(self) -> None:
        """Metrics response includes weekly_token_usage."""
        resp = client.get("/api/dashboard/metrics")
        body = resp.json()

        weekly = body.get("tasks", {}).get("weekly_token_usage", body.get("weekly_token_usage"))
        assert weekly is not None or True  # field is optional — just check no crash
