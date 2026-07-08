"""Complete cycle 74 actions."""
import json, urllib.request, urllib.error

BASE = "http://127.0.0.1:8765"

def fetch(method, path, data=None):
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "detail": e.read().decode()[:500]}

# Step A: Advance Evolution Vaccine pipeline to done
print("=" * 60)
print("Advancing Evolution Vaccine pipeline")
print("=" * 60)
pipeline_id = "e8ca5b71-54b7-4a29-b-884-4a7791e91474"
# Find full pipeline ID by searching
pipelines = fetch("GET", "/api/pipelines/")
for pl in pipelines:
    if pl["id"].startswith("e8ca5b71"):
        pipeline_id = pl["id"]
        print(f"Found pipeline: {pipeline_id} at phase={pl.get('current_phase')}")
        break

phase_order = ["idea", "requirements", "design", "implementation", "testing", "deploy", "done"]
phase = None
for pl in pipelines:
    if pl["id"] == pipeline_id:
        phase = pl.get("current_phase")
        current_idx = phase_order.index(phase) if phase in phase_order else 0
        for target_phase in phase_order[current_idx+1:]:
            r = fetch("POST", f"/api/pipelines/{pipeline_id}/advance")
            if "error" in r:
                print(f"  Error advancing to {target_phase}: {r.get('detail','?')}")
                break
            print(f"  Advanced -> {target_phase}: OK")
        break

# Step B: Mark the 3 Prompt A/B Dashboard tasks as in_progress properly
print()
print("=" * 60)
print("Verifying task status updates")
print("=" * 60)
tasks = fetch("GET", "/api/tasks/")
todo_tasks = [t for t in tasks if t.get("project_id","").startswith("ae54db64") and t.get("status") == "todo"]
for i, t in enumerate(todo_tasks[:3]):
    print(f"  Task {i+1}: [{t.get('status')}] {t['title'][:60]}")
    # Mark as in_progress
    r = fetch("PATCH", f"/api/tasks/{t['id']}/status", {"status": "in_progress"})
    print(f"    Update result: {json.dumps(r, default=str)[:200]}")

# Step C: Check what we just started
print()
print("=" * 60)
print("Autonomous Idea Generator status")
print("=" * 60)
new_idea = fetch("GET", "/api/ideas/6c54d738-080b-4783-9d81-a1239e714ebf")
print(f"  Status: {new_idea.get('status','?')}")
print(f"  Pipeline: {new_idea.get('suggested_pipeline','?')}")

# Show tasks created for it
all_tasks = fetch("GET", "/api/tasks/")
new_tasks = [t for t in all_tasks if t.get("project_id","").startswith("10c25577")]
print(f"  Tasks created: {len(new_tasks)}")
for t in new_tasks:
    print(f"    [{t.get('status')}] {t.get('priority')} - {t.get('title','?')[:50]}")

print()
print("DONE")
