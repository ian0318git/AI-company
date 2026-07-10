#!/usr/bin/env python3
"""Revive the best archived idea and start a pipeline."""
import json, urllib.request

BASE = "http://127.0.0.1:8765/api"

def api(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

# Revive the best idea
best_id = "26d7f201-788c-4fa6-9a7f-c9991e3d002f"
best = api("GET", f"/ideas/{best_id}")
print("Reviving:", best.get("title"))

revived = api("POST", "/ideas/", {
    "title": "Revived: Repo Root Cleanup & Report Consolidation (auto-seeded cycle #256)",
    "raw_description": best.get("raw_description", ""),
    "tags": ["revived", "auto-seeded", "maintenance", "housekeeping"],
    "suggested_pipeline": "quick-prototype",
})
new_id = revived.get("id")
print(f"Created: {revived.get('title')} (id=%s)" % new_id)

refined = api("POST", f"/ideas/{new_id}/refine", {
    "refined_description": "Phase 1: Audit all root-level files and categorize (transient vs persistent). Phase 2: Move valuable diagnostic scripts (tmp_*.py) to tools/ directory. Phase 3: Consolidate cycle reports (cycle*-report.md) into docs/cycles/ with summary index. Phase 4: Remove confirmed-temporary files via git rm. Phase 5: Update .gitignore patterns to keep root clean. Pure maintenance.",
    "suggested_pipeline": "quick-prototype",
})
print("Refined, status:", refined.get("status"))

started = api("POST", f"/ideas/{new_id}/start", {})
print(f"Started pipeline, project_id: {started.get('project_id')}")
