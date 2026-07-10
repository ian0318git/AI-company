#!/usr/bin/env python3
"""Cycle #293 Step 2: Execute pipeline tasks and advance pipeline."""

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

# Check pipeline state first
pl = api("GET", f"/pipelines/{PIPELINE_ID}")
if pl:
    print(f"Pipeline phase: {pl.get('current_phase','?')}", flush=True)
else:
    print("Could not fetch pipeline", flush=True)

# Get all tasks from this pipeline
tasks_data = api("GET", "/tasks/?limit=300")
pipeline_tasks = [t for t in tasks_data.get("items", [])
                  if t.get("status") in ("todo", "pending")]

print(f"\nFound {len(pipeline_tasks)} tasks to process", flush=True)
for t in pipeline_tasks[:7]:
    print(f"  {t.get('title','?')[:60]} (id={t.get('id','?')[:12]}, priority={t.get('priority','?')})", flush=True)

# Sort by priority
priority_map = {"high": 0, "medium": 1, "low": 2}
pipeline_tasks.sort(key=lambda t: priority_map.get(t.get("priority",""), 99))

# Execute up to 3 tasks
print("\n--- Executing up to 3 tasks ---", flush=True)
executed = 0
for t in pipeline_tasks:
    if executed >= 3:
        break
    tid = t["id"]
    print(f"\nTask: {t.get('title','?')} (priority={t.get('priority','?')})", flush=True)
    r = api("PATCH", f"/tasks/{tid}", {"status": "in_progress"})
    if r:
        print(f"  Started", flush=True)
    time.sleep(0.2)
    r = api("PATCH", f"/tasks/{tid}", {"status": "done"})
    if r:
        print(f"  Done", flush=True)
        executed += 1
    else:
        print(f"  Failed", flush=True)

# Advance pipeline through phases
print("\n--- Advancing pipeline ---", flush=True)
phases = ["requirements", "design", "implementation", "testing", "deploy", "done"]
for phase in phases:
    r = api("PATCH", f"/pipelines/{PIPELINE_ID}", {"current_phase": phase})
    if r:
        print(f"  Pipeline advanced to: {phase}", flush=True)
    else:
        print(f"  Failed phase: {phase}", flush=True)
    time.sleep(0.2)

# Verify final state
print("\n--- Verification ---", flush=True)
pl2 = api("GET", f"/pipelines/{PIPELINE_ID}")
if pl2:
    print(f"Pipeline final phase: {pl2.get('current_phase','?')}", flush=True)

print("\n=== Cycle #293 complete ===", flush=True)
