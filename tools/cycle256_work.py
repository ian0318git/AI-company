#!/usr/bin/env python3
"""Cycle #256 work script."""
import json, urllib.request

BASE = "http://127.0.0.1:8765/api"

def api(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

# 1. Complete the idle detection idea
print("=== Step 1: Complete idle detection idea ===")
result = api("PATCH", "/ideas/da9bf5b6-e6af-4704-8987-53b35ac74981", {"status": "done"})
print("Status:", result.get("status"))

# 2. Check if system is idle
print("\n=== Step 2: Check system state ===")
ideas = api("GET", "/ideas/?limit=50")
tasks = api("GET", "/tasks/?limit=300")
projects = api("GET", "/projects/?limit=50")

active_tasks = [t for t in tasks["items"] if t.get("status") in ("pending","in_progress","paused")]
active_projects = [p for p in projects["items"] if p.get("status") not in ("completed","cancelled")]
pending_ideas = [i for i in ideas["items"] if i.get("status") not in ("done","archived")]

print("Pending tasks:", len(active_tasks))
print("Active projects:", len(active_projects))
print("Pending ideas:", len(pending_ideas))
is_idle = len(active_tasks) == 0 and len(active_projects) == 0 and len(pending_ideas) == 0
print("System idle:", is_idle)

# 3. Score and find best archived idea to revive
print("\n=== Step 3: Find best archived idea ===")
archived = [i for i in ideas["items"] if i.get("status") == "archived"]
# Skip the "test" idea and Chinese ones
def revival_score(idea):
    tags = idea.get("tags", [])
    title = idea.get("title", "").lower()
    score = 0
    if "self-improvement" in tags: score += 10
    if "evolution" in tags: score += 8
    if "maintenance" in tags: score += 10
    if "auto-seed" in tags: score += 15
    if "revived" in tags: score += 5
    if "housekeeping" in tags: score += 6
    if "performance" in tags: score += 5
    if "cleanup" in tags: score += 5
    if "testing" in tags: score += 4
    if "self-healing" in title: score += 12
    if "idle" in title: score += 12
    if "root" in title: score += 8
    if "cleanup" in title or "clean" in title: score += 8
    if "deprecated" in title: score += 6
    return score

# Filter useful archived ideas
useful = [i for i in archived if i.get("title") not in ("test",) and "M5Stack" not in i.get("title","")]
useful.sort(key=revival_score, reverse=True)

for idx, i in enumerate(useful):
    print(f"  {idx+1}. [{revival_score(i)}] {i.get('title','?')[:60]}")

best = useful[0]
best_id = best["id"]
best_title = best["title"]
print(f"\nBest candidate: {best_title} (score={revival_score(best)})")

# 4. Revive it
print("\n=== Step 4: Revive idea ===")
revived = api("POST", "/ideas/", {
    "title": f"Revived: {best_title} (auto-seeded cycle #256)",
    "raw_description": best.get("raw_description", ""),
    "tags": list(set(best.get("tags", []) + ["revived", "auto-seeded"])),
    "suggested_pipeline": best.get("suggested_pipeline", "quick-prototype"),
})
new_id = revived.get("id", "?")
print(f"Created revived idea: {revived.get('title')} (id={new_id})")

# 5. Refine it
print("\n=== Step 5: Refine idea ===")
refined = api("POST", f"/ideas/{new_id}/refine", {
    "refined_description": best.get("refined_description") or best.get("raw_description", ""),
    "suggested_pipeline": best.get("suggested_pipeline", "quick-prototype"),
})
print(f"Refined, status: {refined.get('status')}")

# 6. Start pipeline
print("\n=== Step 6: Start pipeline ===")
started = api("POST", f"/ideas/{new_id}/start", {})
if started:
    print(f"Started pipeline, project_id: {started.get('project_id')}")
    print(json.dumps(started, indent=2)[:500])
else:
    print("Failed to start pipeline")

print("\n=== Done ===")
