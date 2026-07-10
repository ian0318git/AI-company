"""WebSocket endpoints for real-time dashboard updates.

Provides a /ws/dashboard endpoint that pushes live metrics to connected
dashboard clients: agent status, token burn rate, task progress, and
cycle timeline events.
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.storage import get_session, get_sessionmaker
from ai_embedded_company.storage.models import TaskModel, IdeaModel, PipelineModel

router = APIRouter()


# ── Connection manager ──────────────────────────────────────────────────

class ConnectionManager:
    """Manages active WebSocket connections and broadcasts."""

    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket, client_id: str) -> None:
        await ws.accept()
        async with self._lock:
            self._connections[client_id] = ws

    async def disconnect(self, client_id: str) -> None:
        async with self._lock:
            self._connections.pop(client_id, None)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send a JSON message to every connected client."""
        dead: list[str] = []
        async with self._lock:
            for cid, ws in self._connections.items():
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(cid)
        # Clean up dead connections outside the lock
        for cid in dead:
            await self.disconnect(cid)

    @property
    def client_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()


# ── WebSocket endpoint ─────────────────────────────────────────────────

@router.websocket("/dashboard")
async def dashboard_ws(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time dashboard updates.

    On connect, the client receives an initial snapshot of metrics,
    followed by periodic delta updates every 5 seconds while connected.
    """
    client_id = f"ws_{id(websocket)}_{time.time():.0f}"
    await manager.connect(websocket, client_id)
    try:
        while True:
            # Consume any incoming messages (keepalive pings)
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(), timeout=5.0
                )
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                pass  # No message within interval — that's normal

            # Build and broadcast the current snapshot
            snapshot = await _build_metrics_snapshot()
            await websocket.send_json(snapshot)
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(client_id)


# ── Metric snapshot builders ───────────────────────────────────────────

async def _build_metrics_snapshot(
    session: AsyncSession | None = None,
) -> dict[str, Any]:
    """Build a snapshot of current dashboard metrics.

    Runs a lightweight query that completes under 200ms on moderate data.

    Parameters
    ----------
    session : optional
        An existing DB session to use (for testing).  When omitted a new
        session is acquired directly (not via the ``get_session`` generator,
        to avoid ``IllegalStateChangeError`` on task cancellation).
    """
    from sqlalchemy.exc import IllegalStateChangeError as _IllegalStateChangeError

    if session is None:
        sm = get_sessionmaker()
        try:
            async with sm() as session:
                return await _build_snapshot(session)
        except _IllegalStateChangeError:
            return {"type": "snapshot", "db_available": False,
                    "error": "Session closed during cancellation"}
    return await _build_snapshot(session)


async def _build_snapshot(session: AsyncSession) -> dict[str, Any]:
    """Core snapshot logic — runs queries against *session*."""
    try:
        # ── Task pulse ─────────────────────────────────────────────
        task_result = await session.execute(select(TaskModel))
        tasks = task_result.scalars().all()

        status_counts: dict[str, int] = {}
        total_tokens = 0
        running_count = 0
        for t in tasks:
            s = t.status or "todo"
            status_counts[s] = status_counts.get(s, 0) + 1
            total_tokens += t.tokens_used or 0
            if t.status == "in_progress":
                running_count += 1

        # ── Idea counts ────────────────────────────────────────────
        idea_result = await session.execute(select(IdeaModel))
        ideas = idea_result.scalars().all()
        idea_status_counts: dict[str, int] = {}
        for idea in ideas:
            s = idea.status or "new"
            idea_status_counts[s] = idea_status_counts.get(s, 0) + 1

        # ── Pipeline counts ────────────────────────────────────────
        pipe_result = await session.execute(select(PipelineModel))
        pipelines = pipe_result.scalars().all()
        pipeline_phase_counts: dict[str, int] = {}
        for p in pipelines:
            phase = p.current_phase or "unknown"
            pipeline_phase_counts[phase] = pipeline_phase_counts.get(phase, 0) + 1

        # ── Per-agent telemetry ────────────────────────────────────
        in_prog_result = await session.execute(
            select(TaskModel).where(TaskModel.status == "in_progress")
        )
        in_prog_tasks = in_prog_result.scalars().all()

        agents_telemetry: list[dict[str, Any]] = []
        total_tokens_burn: dict[str, int] = {}
        now = datetime.now(timezone.utc)
        for t in in_prog_tasks:
            agent = t.assigned_agent or "unassigned"
            elapsed = 0.0
            if t.started_at:
                # started_at is timezone-naive from SQLite — treat as UTC
                if t.started_at.tzinfo is None:
                    started = t.started_at.replace(tzinfo=timezone.utc)
                else:
                    started = t.started_at
                elapsed = (now - started).total_seconds()
            agents_telemetry.append({
                "agent": agent,
                "task_title": t.title,
                "task_id": t.id,
                "elapsed_seconds": round(elapsed, 1),
                "tokens_used": t.tokens_used or 0,
            })
            total_tokens_burn[agent] = total_tokens_burn.get(agent, 0) + (t.tokens_used or 0)
    except Exception as exc:
        # If DB is unavailable, return a minimal health snapshot
        return {"type": "snapshot", "db_available": False, "error": str(exc)}

    return {
        "type": "snapshot",
        "db_available": True,
        "timestamp": time.time(),
        "tasks": {
            "by_status": status_counts,
            "running_count": running_count,
            "total_tokens": total_tokens,
            "total": len(tasks),
        },
        "ideas": {
            "total": len(ideas),
            "by_status": idea_status_counts,
        },
        "pipelines": {
            "total": len(pipelines),
            "by_phase": pipeline_phase_counts,
        },
        "agents": agents_telemetry,
        "agent_token_burn": total_tokens_burn,
    }
