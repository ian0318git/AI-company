#!/usr/bin/env python3
"""Check overall system state for cycle 5."""
import json, urllib.request

BASE = "http://127.0.0.1:8765/api"

def get(path):
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return json.loads(r.read())

print("=== IDEAS ===")
ideas = get("/ideas/")
for i in ideas:
    if i["status"] != "done":
        print(f"  [{i['status']}] {i['title']} (id={i['id'][:8]}...)")
print(f"  Total: {len(ideas)}, done: {sum(1 for i in ideas if i['status']=='done')}")

print("\n=== TASKS ===")
tasks = get("/tasks/")
pending = [t for t in tasks if t["status"] != "done"]
print(f"  Pending: {len(pending)}")
for t in pending[:15]:
    print(f"  [{t['status']}] {t['title']} (proj={t['project_id'][:8]}...)")
print(f"  Total: {len(tasks)}, done: {sum(1 for t in tasks if t['status']=='done')}")

print("\n=== PROJECTS ===")
projects = get("/projects/")
active = [p for p in projects if p["status"] != "completed"]
for p in active:
    print(f"  [{p['status']}] {p['name']} (id={p['id'][:8]}...)")
print(f"  Total: {len(projects)}, completed: {sum(1 for p in projects if p['status']=='completed')}")

print("\n=== PIPELINES ===")
pipelines = get("/pipelines/")
phases = {}
for p in pipelines:
    ph = p.get("current_phase", "?")
    phases[ph] = phases.get(ph, 0) + 1
print(f"  Phases: {json.dumps(phases)}")
print(f"  Total: {len(pipelines)}")

print("\n=== HEALTH ===")
with urllib.request.urlopen("http://127.0.0.1:8765/health") as r:
    h = json.loads(r.read())
print(json.dumps(h, indent=2))
