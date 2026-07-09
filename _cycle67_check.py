#!/usr/bin/env python3
import json, sys

data = json.load(sys.stdin)

# Filter for todo/pending tasks
tasks = [t for t in data if t.get("status") in ("todo", "pending")]
tasks.sort(key=lambda t: {"high": 0, "medium": 1, "low": 2}.get(t.get("priority", "low"), 3))

print(f"Found {len(tasks)} todo/pending tasks:")
for t in tasks[:15]:
    pid = t.get("project_id", "none")[:8] if t.get("project_id") else "none"
    print(f'  [{t["status"]}] {t["title"]} (priority={t["priority"]}, project={pid}, id={t["id"][:8]})')

if not tasks:
    print("  (none)")
    print("---All tasks processed---")

# Also check for in_progress tasks
in_progress = [t for t in data if t.get("status") == "in_progress"]
if in_progress:
    print(f"\nIn-progress tasks ({len(in_progress)}):")
    for t in in_progress:
        print(f'  {t["title"]} (id={t["id"][:8]})')
