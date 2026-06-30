"""System health and status routes."""

from __future__ import annotations

import json
import platform

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.storage import get_session
from ai_embedded_company.storage.models import EventLogModel
from ai_embedded_company.__init__ import __version__

router = APIRouter()


@router.get("/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "version": __version__,
        "python_version": platform.python_version(),
    }


@router.get("/status")
async def system_status():
    """Full system status including database connectivity."""
    try:
        async for session in get_session():
            await session.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
            db_status = "connected"
            break
    except Exception:
        db_status = "disconnected"

    return {
        "api": "running",
        "database": db_status,
        "version": __version__,
    }


@router.post("/event", status_code=201)
async def log_event(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Log a lifecycle event from a hook or tool."""
    body = await request.json()
    event = EventLogModel(
        event_type=body.get("event_type", "unknown"),
        source=body.get("source", ""),
        payload=body.get("payload", "{}"),
    )
    session.add(event)
    await session.commit()
    return {"status": "logged", "id": event.id}
