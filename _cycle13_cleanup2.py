#!/usr/bin/env python3
"""Clean up stale tasks and advance remaining pipelines using correct API methods."""
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
            return {"status": "ok", "code": r.getcode()}
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} on {method} {path}: {e.read().decode()[:100]}")
        return None
    except Exception as e:
        print(f"  ERR {method} {path}: {e}")
        return None

# 1. Cancel stale tasks from completed project acb3fe13
tasks = fetch("/tasks/")
stale = [t for t in tasks if t['project_id'] == 'acb3fe13-d6fb-46ad-b341-c7b014630449' and t.get('status') == 'todo']
print(f"Stale tasks from completed project: {len(stale)}")
cancelled = 0
for t in stale:
    r = fetch(f"/tasks/{t['id']}/status", method="PATCH", data=json.dumps({"status": "cancelled"}).encode())
    if r:
        cancelled += 1
print(f"Cancelled: {cancelled}")

# 2. Complete remaining pipelines (advance to done)
pipelines = fetch("/pipelines/")
active_p = [p for p in pipelines if p.get('current_phase') not in ('done', 'completed')]
print(f"\nActive pipelines to complete: {len(active_p)}")
for p in active_p:
    r = fetch(f"/pipelines/{p['id']}/advance", method="POST", data=json.dumps({"to_phase": "done"}).encode())
    if r:
        print(f"  {p['id'][:8]} ({p.get('pipeline_type')}): now {r.get('current_phase','?')}")
    else:
        # Try through all phases
        for phase in ["requirements", "design", "implementation", "testing", "deploy"]:
            r = fetch(f"/pipelines/{p['id']}/advance", method="POST", data=json.dumps({"to_phase": phase}).encode())
            if r:
                print(f"  {p['id'][:8]} advanced to {phase}: {r.get('current_phase','?')}")
        # Final done
        r = fetch(f"/pipelines/{p['id']}/advance", method="POST", data=json.dumps({"to_phase": "done"}).encode())
        if r:
            print(f"  {p['id'][:8]} final: {r.get('current_phase','?')}")

# 3. Check final state
print(f"\n=== FINAL STATE ===")
tasks = fetch("/tasks/")
active_t = [t for t in tasks if t.get('status') not in ('done', 'completed', 'cancelled')]
print(f"Tasks: {len(tasks)} total, {len(active_t)} active")
for t in active_t[:5]:
    print(f"  [{t['id'][:8]}] {t['title'][:50]} ({t.get('status','?')})")

pipelines = fetch("/pipelines/")
active_p = [p for p in pipelines if p.get('current_phase') not in ('done', 'completed')]
print(f"Pipelines: {len(pipelines)} total, {len(active_p)} active")

projects = fetch("/projects/")
active_pr = [p for p in projects if p.get('status') not in ('completed', 'done')]
print(f"Projects: {len(projects)} total, {len(active_pr)} active")
for pr in active_pr:
    print(f"  [{pr['id'][:8]}] {pr.get('name','?')} ({pr.get('status','?')})")
