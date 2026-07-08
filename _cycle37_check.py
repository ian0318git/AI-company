#!/usr/bin/env python3
import json, sys, urllib.request

BASE = "http://127.0.0.1:8765"

def api(path):
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return json.loads(r.read())

# --- Tasks ---
tasks = api("/api/tasks/")
todo = [t for t in tasks if t.get("status") == "todo"]
print(f"Tasks: {len(tasks)} total, {len(todo)} todo")
print(f"\nTodo tasks (project: {todo[0]['project_id'][:8]}...):")
for t in todo:
    print(f"  [{t['priority']}] {t['title']} (id: {t['id'][:8]}...)")

# --- Project for those tasks ---
projects = api("/api/projects/")
for p in projects:
    if p.get("id") == todo[0]["project_id"]:
        print(f"\nProject: {json.dumps(p, indent=2)}")
        break

# --- Ideas ---
ideas = api("/api/ideas/")
in_progress = [i for i in ideas if i.get("status") != "done"]
print(f"\nIdeas: {len(ideas)} total, {len(in_progress)} not done")
for i in in_progress:
    print(f"  [{i['status']}] {i['title']} (id: {i['id'][:8]}...)")

# --- Pipelines ---
pipelines = api("/api/pipelines/")
not_done = [p for p in pipelines if p.get("current_phase") != "done"]
print(f"\nPipelines: {len(pipelines)} total, {len(not_done)} not done")

# --- Check endpoints ---
for ep in ["/", "/api/evolution/", "/api/projects/", "/api/ideas/",
           "/api/tasks/", "/api/pipelines/", "/api/health"]:
    try:
        with urllib.request.urlopen(f"{BASE}{ep}") as r:
            data = json.loads(r.read())
            if isinstance(data, list):
                print(f"  {ep} -> {len(data)} items")
            elif isinstance(data, dict):
                print(f"  {ep} -> {list(data.keys())[:5]}")
    except Exception as e:
        print(f"  {ep} -> ERROR: {e}")
