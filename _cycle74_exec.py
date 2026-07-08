"""Cycle 74 execution script."""
import json, urllib.request, urllib.error

BASE = "http://127.0.0.1:8765"

def fetch(method, path, data=None):
    """Make an HTTP request to the API."""
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "detail": e.read().decode()[:500]}

# ---- Step 1: Start the Autonomous Idea Generator idea ----
print("=" * 60)
print("STEP 1: Starting Autonomous Idea Generator pipeline")
print("=" * 60)
res = fetch("POST", "/api/ideas/6c54d738-080b-4783-9d81-a1239e714ebf/start")
print(json.dumps({"status": res.get("idea",{}).get("status","?"),
                   "pipeline_type": res.get("pipeline",{}).get("pipeline_type","?"),
                   "tasks_created": len(res.get("tasks",[])),
                   "team_members": len(res.get("team",{}).get("members",[]))}, indent=2))

# ---- Step 2: Find and advance Evolution Vaccine pipeline ----
print()
print("=" * 60)
print("STEP 2: Advancing Evolution Vaccine Injection pipeline")
print("=" * 60)

# Find the pipeline for the Evolution Vaccine idea
pipelines = fetch("GET", "/api/pipelines/")
ev_idea_id = "eff87aaf-f5df-466e-a508-5d1f1c232585"
ev_pipeline = None
for p in pipelines:
    if p.get("idea_id", "").startswith("eff87aaf"):
        ev_pipeline = p
        break

if ev_pipeline:
    pid = ev_pipeline["id"]
    phase = ev_pipeline["current_phase"]
    print(f"Found pipeline: {pid[:20]}... at phase: {phase}")
    # Advance from current phase to done
    phase_order = ["idea", "requirements", "design", "implementation", "testing", "deploy", "done"]
    current_idx = phase_order.index(phase) if phase in phase_order else 0
    for target_phase in phase_order[current_idx+1:]:
        r = fetch("POST", f"/api/pipelines/{pid}/advance")
        print(f"  Advanced -> {target_phase}: {r.get('message','?')}")
else:
    print("ERROR: Evolution Vaccine pipeline not found!")

# ---- Step 3: Start executing Prompt A/B Dashboard tasks ----
print()
print("=" * 60)
print("STEP 3: Executing Prompt A/B Dashboard todo tasks")
print("=" * 60)

tasks = fetch("GET", "/api/tasks/")
project_prefix = "ae54db64"
todo_tasks = [t for t in tasks if t.get("project_id","").startswith(project_prefix) and t.get("status") == "todo"]
print(f"Found {len(todo_tasks)} todo tasks for Prompt A/B Dashboard project")
for i, t in enumerate(todo_tasks[:3]):
    print(f"\n  Task {i+1}: {t['title']} (id={t['id'][:12]}...)")
    # Mark as in_progress
    r = fetch("PATCH", f"/api/tasks/{t['id']}/status", {"status": "in_progress"})
    print(f"    -> {r.get('status','?')}")

print()
print("DONE - Cycle 74 execution complete")
