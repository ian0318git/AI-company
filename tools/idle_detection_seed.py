#!/usr/bin/env python3
"""
Auto-Seed: Idle Detection & Work Generator

After 4+ consecutive idle autonomous cycles, this module detects the fully-drained
state and generates seed tasks from archived ideas by revival priority.

Part of Cycle 255 — Self-Healing Idle Detection System implementation.
"""

import json
import urllib.request
import urllib.error
import sys
from datetime import datetime, timezone
from typing import Any

BASE = "http://127.0.0.1:8765/api"


def api(method: str, path: str, body: dict | None = None) -> dict[str, Any] | None:
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  API error {e.code} on {method} {path}: {err[:200]}", file=sys.stderr)
        return None


def check_idle_state() -> dict[str, Any]:
    """Check if the system is in a fully idle state."""
    ideas = api("GET", "/ideas/?limit=50")
    tasks = api("GET", "/tasks/?limit=300")
    projects = api("GET", "/projects/?limit=50")

    active_tasks = [
        t for t in (tasks or {}).get("items", [])
        if t.get("status") in ("pending", "in_progress", "paused")
    ]
    active_projects = [
        p for p in (projects or {}).get("items", [])
        if p.get("status") not in ("completed", "cancelled")
    ]
    pending_ideas = [
        i for i in (ideas or {}).get("items", [])
        if i.get("status") not in ("done", "archived")
    ]

    all_ideas = (ideas or {}).get("items", [])
    auto_seed_candidates = [
        i for i in all_ideas
        if i.get("status") == "archived"
        and "auto-seed" in i.get("tags", [])
    ]

    return {
        "is_idle": len(active_tasks) == 0
                   and len(active_projects) == 0
                   and len(pending_ideas) == 0,
        "active_tasks": len(active_tasks),
        "active_projects": len(active_projects),
        "pending_ideas": len(pending_ideas),
        "total_ideas": len(all_ideas),
        "total_tasks": len((tasks or {}).get("items", [])),
        "total_projects": len((projects or {}).get("items", [])),
        "auto_seed_candidates": len(auto_seed_candidates),
        "auto_seed_candidate_ids": [i["id"] for i in auto_seed_candidates],
    }


def get_archived_ideas() -> list[dict[str, Any]]:
    """Get all archived ideas sorted by revival priority."""
    ideas = api("GET", "/ideas/?limit=50")
    if not ideas:
        return []

    archived = [
        i for i in ideas.get("items", [])
        if i.get("status") == "archived"
    ]

    def revival_score(idea: dict[str, Any]) -> int:
        """Score archived ideas for revival priority."""
        tags = idea.get("tags", [])
        title = idea.get("title", "").lower()
        score = 0

        # Core maintenance tasks score highest
        if "maintenance" in tags:
            score += 10
        if "self-improvement" in tags:
            score += 10
        if "evolution" in tags:
            score += 8
        if "housekeeping" in tags:
            score += 6
        if "performance" in tags:
            score += 5
        if "cleanup" in tags:
            score += 5
        if "testing" in tags:
            score += 4

        # Auto-seed tagged ideas get a bonus (they were designed for this)
        if "auto-seed" in tags:
            score += 15

        # Ideas that were revived before get higher priority
        if "revived" in tags:
            score += 5

        # Specific keywords in title
        if "self-healing" in title or "idle" in title:
            score += 12
        if "cleanup" in title or "clean" in title:
            score += 8
        if "root" in title:
            score += 5
        if "dependency" in title:
            score += 3

        return score

    archived.sort(key=revival_score, reverse=True)
    return archived


def auto_revive_best_idea() -> None:
    """Auto-revive the highest-scoring archived idea and start a pipeline."""
    archived = get_archived_ideas()
    if not archived:
        print("No archived ideas to revive.")
        return

    best = archived[0]
    title = best.get("title", "Untitled")
    print(f"Top revival candidate: {title} (score={archived.index(best)+1})")

    # Check if there's already an active pipeline for this idea
    # by looking for in_progress ideas with similar titles
    ideas = api("GET", "/ideas/?limit=50")
    if ideas:
        in_progress = [
            i for i in ideas.get("items", [])
            if i.get("status") == "in_progress"
        ]
        if in_progress:
            print(f"Already have {len(in_progress)} in-progress idea(s):")
            for ip in in_progress:
                print(f"  - {ip.get('title', '?')}")
            print("Skipping auto-revive to avoid overloading.")
            return

    # Create a revived idea
    # Strip existing "Revived: " prefix and "(auto-seeded cycle #N)" suffix to prevent
    # duplicated prefixes like "Revived: Revived: ..."
    import re
    clean_title = title
    while clean_title.startswith("Revived: "):
        clean_title = clean_title[9:]
    clean_title = re.sub(r'\s*\(auto-seeded cycle #\d+\)\s*', '', clean_title).strip()
    revived_idea = {
        "title": f"Revived: {clean_title} (auto-seeded cycle #308)",
        "raw_description": best.get("raw_description", ""),
        "tags": list(set(best.get("tags", []) + ["revived", "auto-seeded"])),
        "suggested_pipeline": best.get("suggested_pipeline", "quick-prototype"),
    }

    result = api("POST", "/ideas/", revived_idea)
    if result:
        print(f"Revived idea: {result.get('title')} (id={result.get('id')})")
        # Refine and start pipeline
        refine = api("POST", f"/ideas/{result['id']}/refine", {
            "refined_description": best.get("refined_description", best.get("raw_description", "")),
            "suggested_pipeline": best.get("suggested_pipeline", "quick-prototype"),
        })
        if refine:
            print(f"Refined idea, status: {refine.get('status')}")
        start = api("POST", f"/ideas/{result['id']}/start", {})
        if start:
            print(f"Started pipeline, project_id: {start.get('project_id')}")
            print(json.dumps(start, indent=2))
    else:
        print(f"Failed to create revived idea for: {title}")


def main() -> None:
    print(f"=== Auto-Seed Idle Detection — {datetime.now(timezone.utc).isoformat()} ===\n")

    state = check_idle_state()
    print(f"System idle: {state['is_idle']}")
    print(f"  Active tasks: {state['active_tasks']}")
    print(f"  Active projects: {state['active_projects']}")
    print(f"  Pending ideas: {state['pending_ideas']}")
    print(f"  Total ideas: {state['total_ideas']}")
    print(f"  Total tasks: {state['total_tasks']}")
    print(f"  Total projects: {state['total_projects']}")
    print(f"  Auto-seed candidates: {state['auto_seed_candidates']}")

    if state["is_idle"]:
        archived = get_archived_ideas()
        print(f"\nArchived ideas available for revival: {len(archived)}")
        for i, idea in enumerate(archived[:5]):
            print(f"  {i+1}. {idea.get('title', '?')[:70]}")

        print("\n--- Auto-reviving best candidate ---")
        auto_revive_best_idea()
    else:
        print("\nSystem is not idle. No auto-revival needed.")


if __name__ == "__main__":
    main()
