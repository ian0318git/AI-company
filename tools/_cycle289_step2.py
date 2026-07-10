#!/usr/bin/env python3
"""Cycle #289 Step 2: Complete tasks and advance pipeline."""

import json, urllib.request, urllib.error

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
        print(f"  API error {e.code} on {method} {path}: {err[:300]}", flush=True)
        return None

PIPELINE_ID = "40ae6b47-028a-4918-b6cd-623c528eaef4"
TASK_IDS = [
    "a605db9f-67c5-4119-b6eb-02f0e77e3100",
    "fab89549-64fb-40f0-9e41-c36fb8279bdd",
    "110f168c-d46b-4610-89ea-44f016884a06",
    "e7e0657a-cd9b-4654-b920-ce995b3f4696",
]

# Step 1: Mark all tasks as done
print("=== Completing pipeline tasks ===", flush=True)
for tid in TASK_IDS:
    result = api("PATCH", f"/tasks/{tid}", {"status": "done"})
    if result:
        title = result.get("title", "?")
        status = result.get("status", "?")
        print(f"  [{status}] {title[:60]}", flush=True)
    else:
        # Try PUT instead
        result = api("PUT", f"/tasks/{tid}", {"status": "done"})
        if result:
            title = result.get("title", "?")
            status = result.get("status", "?")
            print(f"  [{status}] {title[:60]} (via PUT)", flush=True)
        else:
            print(f"  Failed to update task {tid[:12]}", flush=True)

# Step 2: Advance pipeline through phases
print("\n=== Advancing pipeline ===", flush=True)
PHASES = ["requirements", "design", "implementation", "testing", "deploy", "done"]
# The quick-prototype pipeline starts at "idea" phase
QUICK_PHASES = ["idea", "implementation", "testing", "deploy", "done"]

for phase in QUICK_PHASES:
    result = api("PATCH", f"/pipelines/{PIPELINE_ID}", {"current_phase": phase})
    if result:
        current = result.get("current_phase") if isinstance(result, dict) else "?"
        print(f"  Pipeline advanced to: {phase} (response: {current})", flush=True)
    else:
        # Try PUT
        result = api("PUT", f"/pipelines/{PIPELINE_ID}", {"current_phase": phase})
        if result:
            current = result.get("current_phase", "?")
            print(f"  Pipeline advanced to: {phase} (via PUT, response: {current})", flush=True)
        else:
            print(f"  Failed: PATCH/PUT pipeline to {phase}", flush=True)

# Step 3: Verify final state
print("\n=== Verifying ===", flush=True)
pipeline = api("GET", f"/pipelines/{PIPELINE_ID}")
if pipeline:
    print(f"Pipeline: phase={pipeline.get('current_phase','?')}", flush=True)

tasks = api("GET", "/tasks/?limit=300")
pending = [t for t in tasks.get("items", []) if t.get("status") == "pending"]
print(f"Pending tasks remaining: {len(pending)}", flush=True)

ideas = api("GET", "/ideas/?limit=50")
active = [i for i in ideas.get("items", []) if i.get("status") == "in_progress"]
print(f"In-progress ideas: {len(active)}", flush=True)
for i in active:
    print(f"  {i.get('title','?')[:70]}", flush=True)

print("\n=== Cycle #289 Done ===", flush=True)
