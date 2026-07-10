#!/usr/bin/env python3
"""Cycle #293 Step 4: Execute tasks and advance pipeline with correct API endpoints."""

import json, time, urllib.request

BASE = "http://127.0.0.1:8765/api"

def api(method, path, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  API error {e.code}: {err[:200]}", flush=True)
        return None

PIPELINE_ID = "55182f93-8299-4b8d-b7ce-44ffcd84d161"
PROJECT_ID = "876c2337-dbac-4b24-8fd3-aac3ebc0ca05"

# Step 1: Complete 3 tasks
print("=== Completing tasks ===", flush=True)

tasks = api("GET", "/tasks/?limit=500")
project_tasks = [t for t in tasks.get("items", [])
                 if t.get("project_id") == PROJECT_ID and t.get("status") == "todo"]

# Deduplicate by title
seen_titles = set()
unique_tasks = []
for t in project_tasks:
    title = t.get("title", "")
    if title not in seen_titles:
        seen_titles.add(title)
        unique_tasks.append(t)

print(f"Unique tasks: {len(unique_tasks)}", flush=True)

priority_map = {"high": 0, "medium": 1, "low": 2}
unique_tasks.sort(key=lambda t: priority_map.get(t.get("priority", ""), 99))

executed = 0
for t in unique_tasks:
    if executed >= 3:
        break
    tid = t["id"]
    title = t.get("title", "?")
    print(f"\nTask: {title[:60]} (priority={t.get('priority','?')})", flush=True)
    # Use correct endpoint: PATCH /api/tasks/{task_id}/status
    r = api("PATCH", f"/tasks/{tid}/status", {"status": "in_progress"})
    if r:
        print(f"  Started: {r}", flush=True)
    else:
        print(f"  Start failed", flush=True)
    time.sleep(0.2)
    r = api("PATCH", f"/tasks/{tid}/status", {"status": "done"})
    if r:
        print(f"  Completed: {r}", flush=True)
        executed += 1
    else:
        print(f"  Failed to complete", flush=True)

# Step 2: Advance pipeline using correct endpoint
print("\n=== Advancing pipeline ===", flush=True)
# POST /api/pipelines/{pipeline_id}/advance
r = api("POST", f"/pipelines/{PIPELINE_ID}/advance", {})
if r:
    print(f"  Advance result: {r}", flush=True)
else:
    print("  Advance endpoint failed", flush=True)

# Step 3: Verify
print("\n=== Verification ===", flush=True)
pl = api("GET", f"/pipelines/{PIPELINE_ID}")
if pl:
    print(f"Pipeline phase: {pl.get('current_phase', '?')}", flush=True)
    for step in pl.get("steps", []):
        print(f"  Step: {step.get('name','?')[:40]} phase={step.get('phase','?')} status={step.get('status','?')}", flush=True)

# Also check completed tasks
tasks_after = api("GET", "/tasks/?limit=500")
done_tasks = [t for t in tasks_after.get("items", [])
              if t.get("project_id") == PROJECT_ID and t.get("status") == "done"]
print(f"\nCompleted tasks for this project: {len(done_tasks)}", flush=True)
for t in done_tasks:
    print(f"  {t.get('title','?')[:60]}", flush=True)

print("\nDone", flush=True)
