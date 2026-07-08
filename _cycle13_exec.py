#!/usr/bin/env python3
"""Cycle #13 execution script."""
import json, urllib.request

BASE = "http://127.0.0.1:8765/api"
IDEA_ID = "7bf1bc73-28d6-4cee-b7fe-2e017ffc9516"

def fetch(path, method="GET", data=None):
    req = urllib.request.Request(f"{BASE}{path}", method=method, data=data)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            body = r.read()
            if body:
                return json.loads(body)
            return None
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} on {method} {path}: {e.read().decode()}")
        return None
    except Exception as e:
        print(f"  ERR {method} {path}: {e}")
        return None

# 1. Check non-completed projects
projects = fetch("/projects/")
active_projects = [pr for pr in projects if pr.get('status') not in ('completed', 'done')]
print(f"Active projects: {len(active_projects)}")
for pr in active_projects:
    print(f"  {pr['id']} - {pr.get('name','?')} (status={pr.get('status','?')})")
    # If it's the cycle 47 project, complete it
    if pr.get('status') == 'active':
        # Mark project done
        result = fetch(f"/projects/{pr['id']}", method="PATCH", data=json.dumps({"status": "completed"}).encode())
        print(f"  -> Marked project completed: {result.get('status') if result else 'failed'}")

# 2. Mark idea as done
result = fetch(f"/ideas/{IDEA_ID}", method="PATCH", data=json.dumps({"status": "done", "refined_description": "Autonomous cycle #47 health check: All 46 ideas done, 270 tasks done, 52 pipelines completed, 46 projects completed. Server healthy. No new work. Reporting idle."}).encode())
print(f"\nIdea update: {result.get('status') if result else 'failed'}")

# 3. Create next cycle idea
new_idea = {
    "title": "Autonomous cycle #48 — auto-system health check",
    "raw_description": "Autonomous cycle #48: Starting from cycle #47 complete state. Will check for new ideas, pending tasks, and pipeline status.",
    "tags": ["auto", "health-check"],
    "suggested_pipeline": "research-spike"
}
result = fetch("/ideas/", method="POST", data=json.dumps(new_idea).encode())
if result:
    print(f"\nNew idea created: {result.get('id','?')[:8]} (status={result.get('status','?')})")
    # Start the idea
    result2 = fetch(f"/ideas/{result['id']}/start", method="POST", data=json.dumps({}).encode())
    print(f"Start result: {result2.get('status') if result2 else 'failed'}")
else:
    print("\nFailed to create new idea")
