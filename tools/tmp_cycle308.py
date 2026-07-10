#!/usr/bin/env python3
"""Cycle #308: revive idea, start pipeline, execute tasks."""
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
        print(f"  API error {e.code} on {method} {path}: {err[:300]}", file=sys.stderr)
        return None

# Step 1: Create idea about fixing pipeline template task mismatch
print("=== Cycle #308: Fix Pipeline Template Task Mismatch ===\n")
idea = {
    "title": "Fix Pipeline Template Task Mismatch (auto-seeded cycle #308)",
    "raw_description": "Audit found that many completed projects have template-generated tasks that don't match project purpose. Examples: Pipeline-Type Matching project has 'Identify academic databases' tasks. Evolution Self-Feed projects have 'Flash firmware' tasks. Caused by pipeline templates generating generic/cross-wired tasks. Fix: (1) audit pipeline template task definitions, (2) fix task generation to match project type, (3) add validation check ensuring created tasks align with idea description.",
    "tags": ["evolution", "self-improvement", "pipeline-hardening", "auto-seed", "maintenance"],
    "suggested_pipeline": "research-spike",
}
result = api("POST", "/ideas/", idea)
if not result:
    print("FAILED to create idea")
    sys.exit(1)
idea_id = result.get("id")
print(f"1. Created idea: {idea_id} — {result.get('title')}")

# Step 2: Refine the idea
refined = api("POST", f"/ideas/{idea_id}/refine", {
    "refined_description": (
        "Phase 1: Audit all pipeline template task definitions in src/ai_embedded_company/orchestrator/ "
        "to identify which tasks are auto-generated vs hardcoded. "
        "Phase 2: Fix the task generation logic so each pipeline type (research-spike, quick-prototype, "
        "web-fullstack, embedded-firmware) generates tasks matching the idea description, not generic templates. "
        "Phase 3: Add validation that checks created tasks align with project purpose before saving. "
        "Phase 4: Write pytest tests verifying correct task generation for each pipeline type. "
        "Pure software maintenance — no hardware required."
    ),
    "suggested_pipeline": "research-spike",
})
if refined:
    print(f"2. Refined idea: status={refined.get('status')}")

# Step 3: Start pipeline
started = api("POST", f"/ideas/{idea_id}/start", {})
if started:
    project_id = started.get("project_id")
    print(f"3. Started pipeline, project_id={project_id}")
else:
    print("3. Failed to start pipeline")
    sys.exit(1)

# Step 4: Check tasks created
time.sleep(1)
tasks = api("GET", f"/tasks/?project_id={project_id}")
items = tasks.get("items", []) if tasks else []
print(f"4. Created {len(items)} tasks:")
for t in items:
    print(f"   [{t['status']}] {t['title'][:65]}")
    if t.get('description'):
        print(f"       desc: {t['description'][:60]}")

# Step 5: Execute up to 3 high-priority tasks
print("\n5. Executing tasks...")
todo = [t for t in items if t['status'] in ('pending', 'todo')]
print(f"   {len(todo)} actionable tasks")
PYEOF
