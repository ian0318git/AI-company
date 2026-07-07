"""System health and status routes."""

from __future__ import annotations

import json
import os
import platform
import subprocess
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.storage import get_session
from ai_embedded_company.storage.models import EventLogModel
from ai_embedded_company.__init__ import __version__

router = APIRouter()

AUTONOMOUS_LOCK = Path("/tmp/ai-company-autonomous.lock")


@router.get("/autonomous")
async def autonomous_status() -> dict:
    """Check if autonomous.sh is running and return its status."""
    pid = None
    uptime_seconds = None
    status = "stopped"

    # Check lock file first (written by autonomous.sh)
    if AUTONOMOUS_LOCK.exists():
        try:
            data = json.loads(AUTONOMOUS_LOCK.read_text())
            pid = data.get("pid")
            started_at = data.get("started_at")
            if started_at:
                uptime_seconds = int((datetime.utcnow() - datetime.fromisoformat(started_at)).total_seconds())
            # Verify the process is actually alive
            if pid:
                alive = os.path.exists(f"/proc/{pid}") if os.name != "nt" else True
                if not alive:
                    pid = None
                    uptime_seconds = None
                    status = "stopped"
                else:
                    status = "running"
        except Exception:
            pass

    # Fallback: check for claude --loop or autonomous processes
    if status == "stopped":
        try:
            result = subprocess.run(
                ["pgrep", "-af", "autonomous\\|claude.*--loop"],
                capture_output=True, text=True, timeout=3
            )
            lines = [l.strip() for l in result.stdout.split("\n") if l.strip()]
            # Filter out the current process
            my_pid = str(os.getpid())
            lines = [l for l in lines if not l.startswith(my_pid)]
            if lines:
                status = "running"
                parts = lines[0].split(None, 1)
                if parts:
                    pid = int(parts[0])
        except Exception:
            pass

    return {
        "status": status,
        "pid": pid,
        "uptime_seconds": uptime_seconds,
        "command": "cd /home/ian/github-project/AI-company && ./scripts/autonomous.sh",
    }


@router.post("/autonomous/start")
async def autonomous_start() -> dict:
    """Start the autonomous scheduler in the background."""
    script_path = Path.cwd() / "scripts" / "autonomous.sh"
    if not script_path.exists():
        return {"status": "error", "message": f"Script not found: {script_path}"}

    try:
        process = subprocess.Popen(
            ["bash", str(script_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        # Write lock file
        AUTONOMOUS_LOCK.write_text(json.dumps({
            "pid": process.pid,
            "started_at": datetime.utcnow().isoformat(),
        }))
        return {
            "status": "started",
            "pid": process.pid,
            "message": f"Autonomous scheduler started (pid {process.pid})",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/autonomous/stop")
async def autonomous_stop() -> dict:
    """Stop the autonomous scheduler."""
    killed = 0

    # Kill by lock file
    if AUTONOMOUS_LOCK.exists():
        try:
            data = json.loads(AUTONOMOUS_LOCK.read_text())
            pid = data.get("pid")
            if pid:
                try:
                    os.kill(pid, 15)  # SIGTERM
                    killed += 1
                except (ProcessLookupError, PermissionError, OSError):
                    pass
            AUTONOMOUS_LOCK.unlink(missing_ok=True)
        except Exception:
            pass

    # Kill by process name
    try:
        result = subprocess.run(
            ["pgrep", "-af", "autonomous\\.sh\\|claude.*--loop"],
            capture_output=True, text=True, timeout=3
        )
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            pid_str = line.split()[0]
            try:
                os.kill(int(pid_str), 15)
                killed += 1
            except (ProcessLookupError, PermissionError, OSError, ValueError):
                pass
    except Exception:
        pass

    return {"status": "stopped", "processes_killed": killed}


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
