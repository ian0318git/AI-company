#!/usr/bin/env python3
"""Final check and cleanup for cycle 13."""
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
        print(f"  HTTP {e.code}: {e.read().decode()[:100]}")
        return None
    except Exception as e:
        print(f"  ERR: {e}")
        return None

# Check active pipelines
pipelines = fetch("/pipelines/")
active_p = [p for p in pipelines if p.get('current_phase') != 'done']
print(f"Active pipelines: {len(active_p)}")
for p in active_p:
    print(f"  [{p['id'][:8]}] type={p.get('pipeline_type')} phase={p.get('current_phase')} project={p.get('project_id','?')[:8]}")
    # Check associated project
    pr = fetch(f"/projects/{p['project_id']}")
    if pr:
        print(f"    Project: {pr.get('name','?')} status={pr.get('status','?')}")

# Check active tasks
tasks = fetch("/tasks/")
active_tasks = [t for t in tasks if t.get('status') in ('pending','in_progress','todo')]
print(f"\nActive tasks: {len(active_tasks)}")
for t in active_tasks:
    print(f"  [{t['id'][:8]}] [{t.get('priority','?')}] {t['title'][:60]} status={t.get('status','?')} project={t.get('project_id','?')[:8]}")

# Check cycle 48 idea and its pipeline
ideas = fetch("/ideas/")
for i in ideas:
    if '48' in i.get('title',''):
        print(f"\nCycle 48 idea: [{i['id'][:8]}] status={i['status']}")
        # Check what pipeline/team was created
        # Try to see if there's a pipeline for this idea
        for p in pipelines:
            if '48' in str(p.get('project_id','')):
                print(f"  Pipeline: {p['id'][:8]} phase={p.get('current_phase')}")
                # Advance to done
                r = fetch(f"/pipelines/{p['id']}/advance", method="POST",
                          data=json.dumps({"to_phase": "done"}).encode())
                if r:
                    print(f"  Advanced to: {r.get('current_phase','?')}")

# Summary
print("\n=== HEALTH SUMMARY ===")
# Try health endpoint
r = fetch("/health")
print(f"Health endpoint: {r}")
r = fetch("/status")
print(f"Status endpoint: {str(r)[:200]}")

# Check evolution
r = fetch("/evolution/status")
print(f"Evolution status: {str(r)[:200]}")

print(f"\n=== FINAL COUNTS ===")
print(f"Ideas: {len(ideas)} total")
print(f"Tasks: {len(tasks)} total, {len(active_tasks)} active")
print(f"Pipelines: {len(pipelines)} total, {len(active_p)} active")
projects = fetch("/projects/")
active_pr = [pr for pr in projects if pr.get('status') not in ('completed','done')]
print(f"Projects: {len(projects)} total, {len(active_pr)} active")
