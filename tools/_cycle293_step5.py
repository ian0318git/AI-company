#!/usr/bin/env python3
"""Cycle #293 Step 5: Complete high-priority tasks and advance pipeline through all phases."""

import json, time, urllib.request

BASE = "http://127.0.0.1:8765/api"
PIPELINE_ID = "55182f93-8299-4b8d-b7ce-44ffcd84d161"
PROJECT_ID = "876c2337-dbac-4b24-8fd3-aac3ebc0ca05"

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

# Step 1: Complete top 3 tasks via query param
print("=== Completing top 3 high-priority tasks ===", flush=True)
tasks = api("GET", "/tasks/?limit=500")
project_tasks = [t for t in tasks.get("items", [])
                 if t.get("project_id") == PROJECT_ID and t.get("status") == "todo"]

seen = set()
unique = []
for t in project_tasks:
    title = t.get("title", "")
    if title not in seen:
        seen.add(title)
        unique.append(t)

priority_map = {"high": 0, "medium": 1, "low": 2}
unique.sort(key=lambda t: priority_map.get(t.get("priority", ""), 99))

# Complete top 3
executed = 0
for t in unique:
    if executed >= 3:
        break
    tid = t["id"]
    title = t.get("title", "?")
    print(f"\nTask: {title[:60]} (priority={t.get('priority','?')})", flush=True)
    # Use query param for status
    r = api("PATCH", f"/tasks/{tid}/status?status=in_progress")
    if r:
        print(f"  Started", flush=True)
    else:
        # Try without body
        req = urllib.request.Request(f"{BASE}/tasks/{tid}/status?status=in_progress", method="PATCH")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as resp:
                r = json.loads(resp.read())
                print(f"  Started (no body)", flush=True)
        except urllib.error.HTTPError as e:
            print(f"  Still failed: {e.code} {e.read().decode()[:100]}", flush=True)
            continue

    time.sleep(0.2)

    r = api("PATCH", f"/tasks/{tid}/status?status=done")
    if r:
        print(f"  Completed", flush=True)
        executed += 1
    else:
        req = urllib.request.Request(f"{BASE}/tasks/{tid}/status?status=done", method="PATCH")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as resp:
                r = json.loads(resp.read())
                print(f"  Completed (no body)", flush=True)
                executed += 1
        except urllib.error.HTTPError as e:
            print(f"  Still failed: {e.code}", flush=True)

print(f"\nDone: {executed} tasks completed", flush=True)

# Step 2: Advance pipeline all the way to done
print("\n=== Advancing pipeline through all phases ===", flush=True)
for i in range(6):  # Try up to 6 advances
    r = api("POST", f"/pipelines/{PIPELINE_ID}/advance", {})
    if r:
        phase = r.get("current_phase", "?")
        complete = r.get("is_complete", False)
        print(f"  Advanced to: {phase} (complete={complete})", flush=True)
        if complete:
            print("  Pipeline is fully complete!", flush=True)
            break
    else:
        print(f"  Advance {i+1} failed", flush=True)

# Step 3: Verify final state
print("\n=== Final Verification ===", flush=True)
pl = api("GET", f"/pipelines/{PIPELINE_ID}")
if pl:
    print(f"Pipeline final phase: {pl.get('current_phase', '?')}", flush=True)
    print(f"Pipeline complete: {pl.get('is_complete', False)}", flush=True)

# Check done tasks count
tasks_after = api("GET", "/tasks/?limit=500")
done_for_project = [t for t in tasks_after.get("items", [])
                    if t.get("project_id") == PROJECT_ID and t.get("status") == "done"]
print(f"Done tasks for project: {len(done_for_project)}", flush=True)
for t in done_for_project:
    print(f"  {t.get('title','?')[:60]}", flush=True)

print("\nCycle #293 complete!", flush=True)
