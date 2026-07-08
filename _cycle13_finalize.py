#!/usr/bin/env python3
"""Finalize: clean stale tasks, advance idle pipelines, report state."""
import json, urllib.request

BASE = "http://127.0.0.1:8765/api"

def fetch(path, method="GET", data=None):
    req = urllib.request.Request(f"{BASE}{path}", method=method, data=data)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            body = r.read()
            if body:
                return json.loads(body)
            return {"status": "ok"}
    except urllib.error.HTTPError as e:
        return None
    except Exception as e:
        return None

# 1. Advance active pipelines for cycle #48 (quick-prototype) to done
pipelines = fetch("/pipelines/")
for p in pipelines:
    if p.get('current_phase') == 'idea' and p.get('pipeline_type') in ('quick-prototype',):
        # Check project name
        pr = fetch(f"/projects/{p['project_id']}")
        if pr and '48' in str(pr.get('name','')):
            for phase in ["idea", "design", "implementation", "testing", "deploy"]:
                r = fetch(f"/pipelines/{p['id']}/advance", method="POST",
                          data=json.dumps({"to_phase": phase}).encode())
                if r:
                    print(f"  Pipeline {p['id'][:8]} advanced to {phase}: {r.get('current_phase','?')}")
                else:
                    break

# 2. Clean up stale tasks from completed project acb3fe13
tasks = fetch("/tasks/")
stale_tasks = [t for t in tasks if t.get('project_id') == 'acb3fe13-d6fb-46ad-b341-c7b014630449' and t.get('status') == 'todo']
print(f"\nStale tasks from completed project (acb3fe13): {len(stale_tasks)}")
for t in stale_tasks:
    r = fetch(f"/tasks/{t['id']}/status", method="POST",
              data=json.dumps({"status": "cancelled"}).encode())
    if r:
        print(f"  Cancelled: {t['title'][:50]}")

# 3. Advance active pipelines for cycle #47 (research-spike) that are still in 'idea'
#    Since the project is already completed, we can mark them done
for p in pipelines:
    if p.get('current_phase') == 'idea' and p.get('pipeline_type') in ('research-spike',):
        pr = fetch(f"/projects/{p['project_id']}")
        if pr and '47' in str(pr.get('name','')):
            r = fetch(f"/pipelines/{p['id']}/advance", method="POST",
                      data=json.dumps({"to_phase": "done"}).encode())
            if r:
                print(f"  Research-spike pipeline {p['id'][:8]} advanced: {r.get('current_phase','?')}")

# 4. Final state
pipelines = fetch("/pipelines/")
active_p = [p for p in pipelines if p.get('current_phase') != 'done']
tasks = fetch("/tasks/")
active_t = [t for t in tasks if t.get('status') in ('pending','in_progress','todo')]
projects = fetch("/projects/")
active_pr = [p for p in projects if p.get('status') not in ('completed','done')]

print(f"\n=== FINAL STATE ===")
print(f"Ideas total: {len(fetch('/ideas/'))}")
print(f"Tasks total: {len(tasks)}, active: {len(active_t)}")
print(f"Pipelines total: {len(pipelines)}, active: {len(active_p)}")
print(f"Projects total: {len(projects)}, active: {len(active_pr)}")
if active_p:
    for p in active_p:
        print(f"  Pipeline {p['id'][:8]}: {p.get('pipeline_type')} phase={p.get('current_phase')}")
if active_t:
    for t in active_t[:5]:
        print(f"  Task {t['id'][:8]}: {t.get('project_id','?')[:8]} {t['title'][:50]} {t.get('status','?')}")
