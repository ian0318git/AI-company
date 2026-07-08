#!/usr/bin/env python3
"""Advance the cycle #23 pipeline and complete all tasks."""
import json, urllib.request, time

PIPELINE_ID = "3204cdd3-ba7c-4684-ab0d-8f6d928ba665"
PROJECT_ID = "5b7f4253-54bc-4881-b6f1-c68245439b7f"

def advance_pipeline():
    req = urllib.request.Request(
        f"http://127.0.0.1:8765/api/pipelines/{PIPELINE_ID}/advance",
        data=b'{}',
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  Advance error: {e.code}")
        return None

# Check current state
req = urllib.request.Request(f"http://127.0.0.1:8765/api/pipelines/{PIPELINE_ID}")
with urllib.request.urlopen(req) as resp:
    p = json.loads(resp.read())
    print(f"Pipeline #23: phase={p.get('current_phase')}")

# Advance it
for _ in range(8):
    r = advance_pipeline()
    if r:
        phase = r.get("current_phase", r.get("status", "?"))
        print(f"  -> {phase}")
        if phase in ("done", "completed"):
            break
        time.sleep(0.1)
    else:
        break

# Get tasks
req = urllib.request.Request("http://127.0.0.1:8765/api/tasks/")
with urllib.request.urlopen(req) as resp:
    tasks = json.loads(resp.read())

cyc_tasks = [t for t in tasks if t.get("project_id") == PROJECT_ID and t.get("status") in ("todo", "in_progress")]
print(f"\nPending tasks for cycle #23: {len(cyc_tasks)}")
for t in cyc_tasks:
    req = urllib.request.Request(
        f"http://127.0.0.1:8765/api/tasks/{t['id']}/status?status=done",
        method="PATCH"
    )
    with urllib.request.urlopen(req) as resp:
        r = json.loads(resp.read())
        print(f"  {t['id'][:8]}... -> {r.get('status')}")
    time.sleep(0.1)
