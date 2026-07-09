"""Integration test for the /ws/dashboard WebSocket endpoint."""
import pytest
from fastapi.testclient import TestClient

from ai_embedded_company.api.app import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_dashboard_ws_connects_and_receives_snapshot():
    """Connect to the dashboard WebSocket and verify an initial snapshot is received."""
    with client.websocket_connect("/ws/dashboard") as ws:
        data = ws.receive_json()
        assert data["type"] == "snapshot"
        assert "tasks" in data
        assert "ideas" in data
        assert "pipelines" in data
        assert data["db_available"] is True


@pytest.mark.asyncio
async def test_dashboard_ws_returns_consistent_schema():
    """Verify the snapshot schema has all expected keys."""
    with client.websocket_connect("/ws/dashboard") as ws:
        data = ws.receive_json()
        for section in ("tasks", "ideas", "pipelines"):
            assert section in data, f"Missing section: {section}"

        tasks = data["tasks"]
        for key in ("total", "by_status", "total_tokens"):
            assert key in tasks, f"Missing tasks.{key}"

        ideas = data["ideas"]
        for key in ("total", "by_status"):
            assert key in ideas, f"Missing ideas.{key}"
