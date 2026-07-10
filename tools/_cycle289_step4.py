#!/usr/bin/env python3
"""Cycle #289 Step 4: Fix tasks and complete pipeline advance."""

import json, urllib.request, urllib.error, sys

BASE = "http://127.0.0.1:8765/api"

def api(method, path, body=None, query=""):
    url = f"{BASE}{path}?{query}" if query else f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  API error {e.code} on {method} {path}?{query}: {err[:200]}", flush=True)
        return None

TASK_IDS = [
    "a605db9f-67c5-4119-b6eb-02f0e77e3100",
    "fab89549-64fb-40f0-9e41-c36fb8279bdd",
    "110f168c-d46b-4610-89ea-44f016884a06",
    "e7e0657a-cd9b-4654-b920-ce995b3f4696",
]
PIPELINE_ID = "40ae6b47-028a-4918-b6cd-623c528eaef4"

# Step 1: Mark tasks as done via query param
print("=== Completing tasks ===", flush=True)
for tid in TASK_IDS:
    result = api("PATCH", f"/tasks/{tid}/status", query=f"status=done")
    if result:
        title = result.get("title", "?")
        status = result.get("status", "?")
        print(f"  [{status}] {title[:60]}", flush=True)
    else:
        print(f"  Failed: {tid[:12]}", flush=True)

# Step 2: Advance pipeline twice more (testing -> deploy -> done)
print("\n=== Advancing pipeline ===", flush=True)
# Pipeline is currently at "testing" after 4 auto-advances from "idea"
# It advances one step at a time, ignoring body
for i in range(2):
    result = api("POST", f"/pipelines/{PIPELINE_ID}/advance")
    if result:
        if isinstance(result, dict):
            cp = result.get("current_phase", result.get("pipeline", {}).get("current_phase", "?"))
        else:
            cp = str(result)
        print(f"  Advanced: current_phase={cp}", flush=True)
    else:
        print(f"  Failed advance attempt {i+1}", flush=True)

# Step 3: Verify
print("\n=== Final state ===", flush=True)
pipeline = api("GET", f"/pipelines/{PIPELINE_ID}")
if pipeline:
    print(f"Pipeline: phase={pipeline.get('current_phase','?')}", flush=True)

tasks = api("GET", "/tasks/?limit=300")
if tasks:
    pending = [t for t in tasks.get("items", []) if t.get("status") == "pending"]
    print(f"Pending tasks: {len(pending)}", flush=True)

ideas = api("GET", "/ideas/?limit=50")
if ideas:
    active = [i for i in ideas.get("items", []) if i.get("status") == "in_progress"]
    print(f"In-progress ideas: {len(active)}", flush=True)
    done = [i for i in ideas.get("items", []) if i.get("status") == "done"]
    print(f"Done ideas: {len(done)}", flush=True)

print("\n=== Cycle #289 complete ===", flush=True)
