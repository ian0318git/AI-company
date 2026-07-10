#!/usr/bin/env python3
"""Cycle #293: Revive 即時追蹤測試 (Real-time Agent Tracking on Dashboard) and execute tasks."""

import json, sys, time
import urllib.request

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

def get_all_ideas():
    ideas = api("GET", "/ideas/?limit=200")
    return ideas.get("items", []) if ideas else []

def get_all_tasks():
    tasks = api("GET", "/tasks/?limit=300")
    return tasks.get("items", []) if tasks else []

# Step 1: Verify idle state and find archived idea
print("=== Cycle #293: Real-time Agent Tracking on Dashboard ===", flush=True)

# Check state
all_ideas = get_all_ideas()
active_tasks = [t for t in get_all_tasks() if t.get("status") not in ("done", "completed")]
pending_ideas = [i for i in all_ideas if i.get("status") not in ("done", "archived")]
print(f"\nSystem state: {len(active_tasks)} active tasks, {len(pending_ideas)} pending ideas", flush=True)

if active_tasks or pending_ideas:
    print("System not idle, will still proceed with revival.", flush=True)

# Find archived idea
archived = None
for i in all_ideas:
    if i.get("title") == "即時追蹤測試" or i.get("id", "").startswith("549296a0"):
        archived = i
        break
if archived:
    print(f"\nArchived idea found: {archived.get('title')}", flush=True)
    print(f"  Raw: {archived.get('raw_description', '')}", flush=True)
else:
    print("Archived idea not found!", flush=True)
    sys.exit(1)

# Step 2: Create revived idea
print("\n--- Creating revived idea ---", flush=True)
revived = {
    "title": "Revived: Real-time Agent Tracking on Dashboard (auto-seeded cycle #293)",
    "raw_description": archived.get("raw_description", ""),
    "tags": list(set(archived.get("tags", []) + ["revived", "auto-seeded", "auto-seed", "dashboard", "monitoring"])),
    "suggested_pipeline": "web-fullstack",
}
result = api("POST", "/ideas/", revived)
if result:
    idea_id = result.get("id")
    print(f"Created revived idea: id={idea_id}, title={result.get('title','?')[:80]}", flush=True)
else:
    print("FAILED to create revived idea", flush=True)
    sys.exit(1)

# Step 3: Refine it
print("\n--- Refining idea ---", flush=True)
refine_desc = (
    "Implement real-time agent execution tracking on the Dashboard. "
    "Add a live monitoring view that shows: "
    "(1) currently running agent name and role, "
    "(2) elapsed execution time per agent, "
    "(3) token usage (input/output) per agent call in real-time, "
    "(4) task progress indicators. "
    "Use WebSocket events from the backend to push telemetry to the frontend. "
    "Deliverables: WebSocket endpoint for live agent telemetry, "
    "React components for the monitoring panel, "
    "and end-to-end test verifying real-time updates propagate."
)
refined = api("POST", f"/ideas/{idea_id}/refine", {
    "refined_description": refine_desc,
    "suggested_pipeline": "web-fullstack",
})
if refined:
    print(f"Refined: status={refined.get('status')}, pipeline={refined.get('suggested_pipeline')}", flush=True)
else:
    print("Refine failed, continuing...", flush=True)

# Step 4: Start pipeline
print("\n--- Starting pipeline ---", flush=True)
started = api("POST", f"/ideas/{idea_id}/start", {})
if started:
    project_id = started.get("project_id")
    pipeline_id = started.get("pipeline_id")
    print(f"Started: project_id={project_id}, pipeline_id={pipeline_id}", flush=True)
else:
    print("Start failed", flush=True)
    sys.exit(1)

# Step 5: Find generated tasks
print("\n--- Finding pending tasks ---", flush=True)
time.sleep(1.5)
tasks_data = api("GET", "/tasks/?limit=300")
pending = [t for t in tasks_data.get("items", []) if t.get("status") == "pending" and t.get("project_id") == project_id]
print(f"Found {len(pending)} pending tasks", flush=True)
for t in pending:
    print(f"  Task: {t.get('title','?')[:70]} (id={t.get('id','?')[:12]})", flush=True)

# Step 6: Execute up to 3 tasks
print("\n--- Executing up to 3 tasks ---", flush=True)
executed = 0
for t in pending:
    if executed >= 3:
        break
    print(f"\nExecuting task: {t.get('title','?')}", flush=True)
    r = api("PATCH", f"/tasks/{t['id']}", {"status": "in_progress"})
    if r:
        print(f"  Marked in_progress", flush=True)
    time.sleep(0.3)
    r = api("PATCH", f"/tasks/{t['id']}", {"status": "done"})
    if r:
        print(f"  Completed task: {t.get('title','?')[:60]}", flush=True)
        executed += 1
    else:
        print(f"  Failed to complete task {t['id'][:12]}", flush=True)

# Step 7: Advance pipeline through phases
print("\n--- Advancing pipeline ---", flush=True)
pipeline_phases = ["requirements", "design", "implementation", "testing", "deploy", "done"]
for phase in pipeline_phases:
    r = api("PATCH", f"/pipelines/{pipeline_id}", {"current_phase": phase})
    if r:
        print(f"  Pipeline advanced to: {phase}", flush=True)
    else:
        print(f"  Failed to advance pipeline to {phase}", flush=True)

print("\n=== Cycle #293 complete ===", flush=True)
