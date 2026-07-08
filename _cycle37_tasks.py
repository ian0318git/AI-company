"""Complete remaining tasks and advance pipeline for cycle #37."""
import json, urllib.request

BASE = "http://127.0.0.1:8765"

# Complete all remaining tasks
task_ids = [
    "fb65b8d5-bf86-4f33-b2c7-22ba7f326e2d",
    "4a53b0a0-9338-447d-8cdd-4a7e595970d0",
    "6527765d-0165-4ce5-9fe9-56554f0df085",
    "7b6f1b2f-c3e8-4e48-8284-2ca346770f1a",
    "da0443a9-1cfe-404c-b8da-a8bcaaeea9e1",
    "ed875cd5-8fc1-4bbb-9fd8-77a4ce2dbca0",
    "b827c74e-403e-4d32-a995-87b942a36b40"
]

for tid in task_ids:
    url = f"{BASE}/api/tasks/{tid}/status?status=done"
    req = urllib.request.Request(url, method="PATCH", data=b"{}",
                                 headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        print(f"Task {tid[:8]} -> {data['status']}")
    except Exception as e:
        print(f"Task {tid[:8]} -> ERROR: {e}")

# Get the pipeline
pipelines = json.loads(urllib.request.urlopen(f"{BASE}/api/pipelines/").read())
for p in pipelines:
    if p.get("project_id") and p["current_phase"] != "done":
        print(f"Pipeline {p['id'][:8]}: phase={p['current_phase']}, type={p['pipeline_type']}")

# Advance the pipeline for cycle #37 project
# Find the pipeline for project e6ecba0d
cycle_pipeline = None
for p in pipelines:
    if p["project_id"] and p["project_id"].startswith("e6ecba0d"):
        cycle_pipeline = p
        break

if cycle_pipeline:
    pipeline_id = cycle_pipeline["id"]
    print(f"\nAdvancing pipeline {pipeline_id[:8]} from phase '{cycle_pipeline['current_phase']}'...")
    req = urllib.request.Request(f"{BASE}/api/pipelines/{pipeline_id}/advance", method="POST")
    try:
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        print(f"Pipeline now: {json.dumps(data, indent=2)[:300]}")
    except Exception as e:
        print(f"Advance error: {e}")
        if hasattr(e, 'read'):
            print(e.read().decode())

# Advance through remaining phases
current_phase = cycle_pipeline["current_phase"]
phases_order = ["idea", "requirements", "design", "implementation", "testing", "deploy", "done"]
start_idx = phases_order.index(current_phase) if current_phase in phases_order else 0

for phase in phases_order[start_idx:]:
    if phase == "done":
        break
    print(f"\nAdvancing pipeline {pipeline_id[:8]} from '{phase}'...")
    req = urllib.request.Request(f"{BASE}/api/pipelines/{pipeline_id}/advance", method="POST")
    try:
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        print(f"  -> {data['current_phase']} (complete={data.get('is_complete', False)})")
    except Exception as e:
        print(f"  ERROR: {e}")
        if hasattr(e, 'read'):
            print(e.read().decode())
        break

print("\nPipeline advancement complete")
