"""Auto-start the FastAPI backend when the MCP server starts.

When the MCP server runs in stdio mode, it needs the REST API to be
available. This module ensures the API server is running before the
MCP server starts serving tools.
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from ai_embedded_company.config import get_settings

logger = logging.getLogger(__name__)

_API_PROCESS: subprocess.Popen | None = None


def _is_api_healthy(base_url: str) -> bool:
    """Check if the API server is responding to health checks."""
    try:
        req = Request(f"{base_url}/health")
        with urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def _kill_port_occupant(port: int) -> None:
    """Attempt to free a port by killing whatever is listening on it."""
    try:
        import subprocess

        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True, text=True
        )
        pids = result.stdout.strip().split("\n")
        for pid in pids:
            if pid and pid.isdigit():
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    logger.info(f"Killed process {pid} occupying port {port}")
                except OSError:
                    pass
    except Exception:
        pass


def _start_api_server() -> subprocess.Popen:
    """Start the FastAPI server as a background subprocess."""
    settings = get_settings()
    port = settings.api_port

    # Kill anything already on our port
    _kill_port_occupant(port)

    # Find the uvicorn entry point
    cmd = [
        sys.executable, "-m", "uvicorn",
        "ai_embedded_company.api.app:app",
        "--host", settings.api_host,
        "--port", str(port),
        "--log-level", "warning",
    ]

    logger.info(f"Starting API server: {' '.join(cmd)}")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid,
    )

    # Wait for it to become healthy
    deadline = time.time() + 15
    while time.time() < deadline:
        if _is_api_healthy(settings.api_base_url):
            logger.info(f"API server healthy on port {port}")
            return proc
        if proc.poll() is not None:
            raise RuntimeError(f"API server exited with code {proc.returncode}")
        time.sleep(0.2)

    raise TimeoutError(f"API server did not become healthy within 15s on port {port}")


def _ensure_api_running() -> None:
    """Start the API server if it's not already running."""
    global _API_PROCESS
    settings = get_settings()

    if _is_api_healthy(settings.api_base_url):
        logger.info("API server already running")
        return

    _API_PROCESS = _start_api_server()


def _shutdown_api_server() -> None:
    """Stop the API server subprocess if we started it."""
    global _API_PROCESS
    if _API_PROCESS is not None:
        try:
            os.killpg(os.getpgid(_API_PROCESS.pid), signal.SIGTERM)
            _API_PROCESS.wait(timeout=5)
        except Exception:
            try:
                _API_PROCESS.kill()
            except Exception:
                pass
        _API_PROCESS = None
