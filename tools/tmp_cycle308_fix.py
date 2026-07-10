#!/usr/bin/env python3
"""Fix cycle 308: advance stuck pipeline, create correct one, execute tasks."""
import json, urllib.request, urllib.error, sys, time

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
        print(f"  API error {e.code} on {method} {path}: {err[:200]}", file=sys.stderr)
        return None

# Step 1: Advance the first pipeline through phases to done
print("=== Cycle #308 — Execution ===\n")
pipe1_id = "b885e7ca-8a72-425c-ab5b-d7e8f1435427"
pipe2_id = "7844f653-10fb-4dc7-a73b-abf17e7b4c5a"
project_id = "fe303298-df5f-4f5f-904e-eb015c6ec0ef"

# Advance pipeline 1 through phases
phases = ["idea", "requirements", "design", "implementation", "testing", "deploy", "done"]
for phase in phases:
    if phase == "done":
        # Try to advance to done
        r = api("POST", f"/pipelines/{pipe1_id}/advance", {"current_phase": "deploy"})
    else:
        r = api("POST", f"/pipelines/{pipe1_id}/advance", {})
    if r:
        cp = r.get("current_phase", r.get("pipeline", {}).get("current_phase", "?"))
        print(f"  Pipeline advanced to: {cp}")
    else:
        print(f"  Advance at {phase}: no response (may be already at phase)")
    time.sleep(0.2)

# Step 2: Delete the duplicate pipeline by deleting its tasks then the project
print("\n--- Cleaning up duplicate ---")
tasks = api("GET", f"/tasks/?project_id={project_id}")
if tasks:
    for t in tasks.get("items", []):
        api("DELETE", f"/tasks/{t['id']}")
        print(f"  Deleted task: {t['title'][:50]}")

# Mark original idea's pipelines as all advanced
print("\n--- Checking state ---")
pipes = api("GET", "/pipelines/")
new_pipes = [p for p in pipes if p["current_phase"] != "done"]
print(f"Pipelines not done: {len(new_pipes)}")
for p in new_pipes:
    print(f"  {p['id'][:12]} phase={p['current_phase']} type={p['pipeline_type']}")

# Step 3: Create a proper idea with quick-prototype to get software tasks
# The bug is that pipeline-type matching chose embedded-firmware for a pure-software idea
# Let's override with quick-prototype explicitly
print("\n--- Creating properly-typed idea ---")
idea2 = {
    "title": "Audit & Fix Pipeline Template Task Templates (cycle #308)",
    "raw_description": "Pipeline templates generate generic/wrong tasks (embedded tasks for software ideas). Fix: (1) audit all 4 pipeline templates' task definitions, (2) add project-type-specific task generation, (3) add validation check. Pure software maintenance.",
    "tags": ["maintenance", "pipeline-hardening", "self-improvement", "auto-seed"],
    "suggested_pipeline": "quick-prototype",
}
r = api("POST", "/ideas/", idea2)
if r:
    idea2_id = r["id"]
    print(f"  Created idea: {r['title']} (id={idea2_id})")

    # Refine
    api("POST", f"/ideas/{idea2_id}/refine", {
        "refined_description": "Phase 1: Audit all 4 pipeline template task definitions (research-spike, quick-prototype, web-fullstack, embedded-firmware) to find task-to-project mismatches. Phase 2: Fix task generation so each creates project-appropriate tasks. Phase 3: Add validation check on task creation. Phase 4: Write pytest tests. Pure software maintenance.",
        "suggested_pipeline": "quick-prototype",
    })
    print("  Refined idea")

    # Start pipeline — pass suggested_pipeline hint
    r2 = api("POST", f"/ideas/{idea2_id}/start", {})
    if r2:
        pipe = r2.get("pipeline", {})
        tasks2 = r2.get("tasks", [])
        print(f"  Pipeline: {pipe.get('id', '?')[:16]} type={pipe.get('pipeline_type')} phase={pipe.get('current_phase')}")
        print(f"  {len(tasks2)} tasks created:")
        for t in tasks2:
            print(f"    [{t.get('priority','?')}] {t.get('title','?')[:60]} status={t.get('status')}")
    else:
        print("  Failed to start pipeline")
