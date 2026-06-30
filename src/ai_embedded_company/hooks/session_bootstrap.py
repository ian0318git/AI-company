#!/usr/bin/env python3
"""SessionStart hook — inject team status + active project context.

This runs when Claude Code starts a new session. It queries the OS API
for active projects, pending tasks, and injects a briefing into context.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

API_BASE = os.environ.get("AI_EMBEDDED_API_URL", "http://127.0.0.1:8765")


def _get(path: str) -> dict | list | None:
    """Call the API and return parsed JSON."""
    try:
        req = urllib.request.Request(
            f"{API_BASE}{path}",
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def main():
    """Generate the session bootstrap context injection."""
    # Check system health first
    health = _get("/health")
    if health is None:
        # API not running — skip injection
        return

    lines = ["[AI Embedded Company — Session Bootstrap]", ""]

    # Active projects
    projects = _get("/api/projects/?status=active")
    if projects and isinstance(projects, list) and len(projects) > 0:
        lines.append("## Active Projects")
        for p in projects[:5]:
            board = f" [{p.get('board_model', '')}]" if p.get('board_model') else ""
            lines.append(f"- **{p['name']}**{board} — {p.get('description', '')[:80]}")
        lines.append("")

    # Pending high-priority tasks
    tasks = _get("/api/tasks/?status=todo")
    high_priority = []
    if tasks and isinstance(tasks, list):
        high_priority = [t for t in tasks if t.get("priority") in ("high", "critical")]
    if high_priority:
        lines.append("## High Priority Tasks")
        for t in high_priority[:5]:
            agent = f" [{t.get('assigned_agent', 'unassigned')}]"
            lines.append(f"- [{t.get('priority', '').upper()}] {t['title']}{agent}")
        lines.append("")

    # Quick start hint
    lines.append("## Quick Start")
    lines.append("- Use `system_health` to check system status")
    lines.append("- Use `project_list` to see all projects")
    lines.append("- Use `task_wall` to view the task board")
    lines.append("- Use `idea_capture` to submit a new idea")
    lines.append("")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
