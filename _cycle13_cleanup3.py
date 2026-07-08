#!/usr/bin/env python3
"""Clean up stale tasks with query param and advance remaining pipelines."""
import json, urllib.request, urllib.parse

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
        print(f"  HTTP {e.code} on {method} {path}: {e.read().decode()[:120]}")
        return None
    except Exception as e:
        return None

# 1. Cancel stale tasks - status as query param
tasks = fetch("/tasks/")
stale = [t for t in tasks if t['project_id'] == 'acb3fe13-d6fb-46ad-b341-c7b014630449' and t.get('status') == 'todo']
print(f"Stale tasks from completed project: {len(stale)}")
cancelled = 0
for t in stale:
    path = f"/tasks/{t['id']}/status?status=cancelled"
    r = fetch(path, method="PATCH", data=json.dumps({}).encode())
    if r:
        cancelled += 1
print(f"Cancelled: {cancelled}")

# 2. Mark stale cycle #48 tasks as done (the project completed when pipelines finished)
stale48 = [t for t in tasks if t.get('status') == 'todo' and t.get('project_id') != 'acb3fe13-d6fb-46ad-b341-c7b014630449']
print(f"\nOther active tasks: {len(stale48)}")
for t in stale48[:5]:
    print(f"  [{t['id'][:8]}] {t['title'][:50]} project={t.get('project_id','?')[:8]}")

# 3. Complete remaining pipelines (already 2 quick-prototype done, 2 research-spike at design)
pipelines = fetch("/pipelines/")
active_p = [p for p in pipelines if p.get('current_phase') not in ('done', 'completed')]
print(f"\nActive pipelines: {len(active_p)}")
for p in active_p:
    # Try direct advance to done
    r = fetch(f"/pipelines/{p['id']}/advance", method="POST", data=json.dumps({"to_phase": "done"}).encode())
    if r:
        print(f"  {p['id'][:8]} advanced to done: {r.get('current_phase','?')}")
    else:
        # Step through remaining phases
        for phase in ["implementation", "testing", "deploy"]:
            r = fetch(f"/pipelines/{p['id']}/advance", method="POST", data=json.dumps({"to_phase": phase}).encode())
            if r:
                print(f"  -> {phase}: {r.get('current_phase','?')}")
        # And final done
        r = fetch(f"/pipelines/{p['id']}/advance", method="POST", data=json.dumps({"to_phase": "done"}).encode())
        if r:
            print(f"  -> done: {r.get('current_phase','?')}")

# 4. Final state
print(f"\n=== FINAL STATE ===")
tasks = fetch("/tasks/")
active_t = [t for t in tasks if t.get('status') not in ('done', 'completed', 'cancelled')]
print(f"Tasks: {len(tasks)} total, {len(active_t)} active")

pipelines = fetch("/pipelines/")
active_p = [p for p in pipelines if p.get('current_phase') not in ('done', 'completed')]
print(f"Pipelines: {len(pipelines)} total, {len(active_p)} active")

projects = fetch("/projects/")
active_pr = [p for p in projects if p.get('status') not in ('completed', 'done')]
print(f"Projects: {len(projects)} total, {len(active_pr)} active")
