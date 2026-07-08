#!/usr/bin/env python3
"""Final status report for autonomous cycle #24."""
import json, urllib.request

IDEAS_URL = "http://127.0.0.1:8765/api/ideas/"
TASKS_URL = "http://127.0.0.1:8765/api/tasks/"
PROJECTS_URL = "http://127.0.0.1:8765/api/projects/"
PIPELINES_URL = "http://127.0.0.1:8765/api/pipelines/"

def get_json(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

ideas = get_json(IDEAS_URL)
tasks = get_json(TASKS_URL)
projects = get_json(PROJECTS_URL)
pipelines = get_json(PIPELINES_URL)

ideas_new = sum(1 for i in ideas if i.get("status") == "new")
ideas_done = sum(1 for i in ideas if i.get("status") == "done")
ideas_prog = sum(1 for i in ideas if i.get("status") in ("in_progress", "refining"))

tasks_pending = sum(1 for t in tasks if t.get("status") in ("todo", "in_progress"))
tasks_done = sum(1 for t in tasks if t.get("status") == "done")

projects_active = sum(1 for p in projects if p.get("status") == "active")
projects_done = sum(1 for p in projects if p.get("status") == "completed")

pipelines_active = sum(1 for p in pipelines if p.get("current_phase") not in ("done", "completed"))

print("=" * 65)
print("  Autonomous Cycle #24 — Final Status Report")
print("=" * 65)
print(f"  Ideas:      {len(ideas)} total — {ideas_new} new, {ideas_prog} in progress, {ideas_done} done")
print(f"  Tasks:      {len(tasks)} total — {tasks_pending} pending, {tasks_done} done")
print(f"  Projects:   {len(projects)} total — {projects_active} active, {projects_done} completed")
print(f"  Pipelines:  {len(pipelines)} total — {pipelines_active} active phase(s)")
print("=" * 65)
