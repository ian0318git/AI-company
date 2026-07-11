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

    # Auto-Seed Idle Detection — check if system is fully idle and seed work
    idle_report = _check_idle_and_seed()
    if idle_report:
        lines.append("## Auto-Seed Idle Detection")
        lines.append(idle_report)
        lines.append("")

    # Quick start hint
    lines.append("## Quick Start")
    lines.append("- Use `system_health` to check system status")
    lines.append("- Use `project_list` to see all projects")
    lines.append("- Use `task_wall` to view the task board")
    lines.append("- Use `idea_capture` to submit a new idea")
    lines.append("")

    print("\n".join(lines))


def _check_idle_and_seed() -> str | None:
    """Check if system is fully idle and auto-seed work if needed.

    Detects fully idle state (no pending tasks, no active projects, no pending ideas)
    and revives the highest-priority archived idea to keep the system running.

    NOTE: Skipped when AI_TEAM_EVOLUTION_PAUSED=true — user wants no auto-execution.
    """
    # Pause switch: user disabled auto-execution
    if os.environ.get("AI_TEAM_EVOLUTION_PAUSED", "").lower() in ("true", "1", "yes"):
        return None

    try:
        ideas = _get("/api/ideas/?limit=50")
        tasks = _get("/api/tasks/?limit=300")
        projects = _get("/api/projects/?limit=50")

        if not ideas or not tasks or not projects:
            return None  # One or more endpoints unavailable

        # Check idle state
        active_tasks = sum(
            1 for t in tasks.get("items", [])
            if t.get("status") in ("pending", "in_progress", "paused")
        )
        active_projects = sum(
            1 for p in projects.get("items", [])
            if p.get("status") not in ("completed", "cancelled")
        )
        pending_ideas = sum(
            1 for i in ideas.get("items", [])
            if i.get("status") not in ("done", "archived")
        )

        is_idle = active_tasks == 0 and active_projects == 0 and pending_ideas == 0

        if not is_idle:
            return None  # System has work — no seeding needed

        # System is idle — find best archived idea to revive
        archived = [
            i for i in ideas.get("items", [])
            if i.get("status") == "archived"
        ]

        if not archived:
            return "System fully idle, but no archived ideas available to revive."

        # Score and sort
        def revival_score(idea: dict) -> int:
            tags = idea.get("tags", [])
            title = idea.get("title", "").lower()
            score = 0
            if "self-improvement" in tags:     score += 10
            if "evolution" in tags:            score += 8
            if "maintenance" in tags:           score += 10
            if "auto-seed" in tags:             score += 15
            if "revived" in tags:              score += 5
            if "housekeeping" in tags:          score += 6
            if "performance" in tags:           score += 5
            if "cleanup" in tags:               score += 5
            if "testing" in tags:               score += 4
            if "self-healing" in title:         score += 12
            if "idle" in title:                 score += 12
            if "root" in title:                 score += 5
            return score

        archived.sort(key=revival_score, reverse=True)
        best = archived[0]

        # Check if this idea was already revived (avoid duplicates)
        in_progress = [
            i for i in ideas.get("items", [])
            if i.get("status") == "in_progress"
        ]
        best_title = best.get("title", "")
        for ip in in_progress:
            if best_title[:30] in ip.get("title", ""):
                return f"Idle detected, but '{best_title[:50]}' is already in progress."

        # Create revived idea via API
        import urllib.request as req_lib

        revived_data = json.dumps({
            "title": f"Auto-seeded: {best_title}",
            "raw_description": best.get("raw_description", ""),
            "tags": list(set(best.get("tags", []) + ["revived", "auto-seeded"])),
            "suggested_pipeline": best.get("suggested_pipeline", "quick-prototype"),
        }).encode()

        try:
            post_req = req_lib.Request(
                f"{API_BASE}/api/ideas/",
                data=revived_data,
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            with req_lib.urlopen(post_req, timeout=10) as resp:
                result = json.loads(resp.read().decode())

            new_id = result.get("id", "?")
            return (
                f"Auto-seeded new idea from '{best_title[:60]}' "
                f"(id={new_id[:12]}). System was fully idle "
                f"({active_tasks} tasks, {active_projects} projects, "
                f"{pending_ideas} pending ideas)."
            )
        except Exception as exc:
            return f"Idle detected but auto-seed failed: {exc}"

    except Exception:
        return None  # Silent failure — don't block bootstrap on auto-seed


if __name__ == "__main__":
    main()
