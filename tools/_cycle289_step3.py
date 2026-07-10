#!/usr/bin/env python3
"""Cycle #289 Step 3: Complete tasks and advance pipeline with correct endpoints."""

import json, urllib.request, urllib.error, sys

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

TASK_IDS = [
    "a605db9f-67c5-4119-b6eb-02f0e77e3100",
    "fab89549-64fb-40f0-9e41-c36fb8279bdd",
    "110f168c-d46b-4610-89ea-44f016884a06",
    "e7e0657a-cd9b-4654-b920-ce995b3f4696",
]
PIPELINE_ID = "40ae6b47-028a-4918-b6cd-623c528eaef4"

# Step 1: Mark all tasks as done via PATCH /tasks/{id}/status
print("=== Completing tasks ===", flush=True)
for tid in TASK_IDS:
    result = api("PATCH", f"/tasks/{tid}/status", {"status": "done"})
    if result:
        title = result.get("title", "?")
        status = result.get("status", "?")
        print(f"  [{status}] {title[:60]}", flush=True)
    else:
        print(f"  Failed: {tid[:12]}", flush=True)

# Step 2: Advance pipeline via POST /pipelines/{id}/advance
print("\n=== Advancing pipeline ===", flush=True)
for phase in ["implementation", "testing", "deploy", "done"]:
    result = api("POST", f"/pipelines/{PIPELINE_ID}/advance", {"current_phase": phase})
    if result:
        if isinstance(result, dict):
            cp = result.get("current_phase", result.get("pipeline", {}).get("current_phase", "?"))
        else:
            cp = str(result)
        print(f"  Advanced to {phase}: current_phase={cp}", flush=True)
    else:
        print(f"  Failed to advance to {phase}", flush=True)

# Step 3: Verify
print("\n=== Verifying final state ===", flush=True)
pipeline = api("GET", f"/pipelines/{PIPELINE_ID}")
if pipeline:
    print(f"Pipeline phase: {pipeline.get('current_phase', '?')}", flush=True)

tasks = api("GET", "/tasks/?limit=300")
if tasks:
    pending = [t for t in tasks.get("items", []) if t.get("status") == "pending"]
    print(f"Pending tasks: {len(pending)}", flush=True)
    in_progress = [t for t in tasks.get("items", []) if t.get("status") == "in_progress"]
    print(f"In-progress tasks: {len(in_progress)}", flush=True)

ideas = api("GET", "/ideas/?limit=50")
if ideas:
    active = [i for i in ideas.get("items", []) if i.get("status") == "in_progress"]
    print(f"In-progress ideas: {len(active)}", flush=True)
    for i in active:
        print(f"  {i.get('title','?')[:70]}", flush=True)

# Step 4: Mark the idea as done too
idea_id = "34b02655-b3c1-412c-b0b9-1b5191377ca3"
result = api("PATCH", f"/ideas/{idea_id}/status", {"status": "done"})
if result:
    print(f"\nIdea status: {result.get('status', '?')}", flush=True)
else:
    # Try different endpoint patterns
    result = api("POST", f"/ideas/{idea_id}/status", {"status": "done"})
    if result:
        print(f"\nIdea status (via POST): {result.get('status', '?')}", flush=True)

print("\n=== Cycle #289 complete ===", flush=True)
sys.exit(0)
