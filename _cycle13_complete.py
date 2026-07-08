#!/usr/bin/env python3
"""Complete cycle 47 and set up cycle 48 properly."""
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
        print(f"  HTTP {e.code} on {method} {path}: {e.read().decode()}")
        return None
    except Exception as e:
        print(f"  ERR {method} {path}: {e}")
        return None

# 1. Get cycle #47 pipeline ID
pipelines = fetch("/pipelines/")
print(f"Total pipelines: {len(pipelines)}")

# Find the newest pipeline (for cycle #47)
cycle47_pipeline = None
for p in pipelines:
    pr = fetch(f"/projects/{p['project_id']}")
    if pr:
        print(f"Pipeline {p['id'][:8]} -> project: {pr.get('name','?')[:40]}")
        if '47' in str(pr.get('name','')):
            cycle47_pipeline = p
            break

if not cycle47_pipeline:
    # Take the newest one
    cycle47_pipeline = max(pipelines, key=lambda p: p.get('created_at', ''))
    print(f"\nNo explicit cycle 47 pipeline. Using newest: {cycle47_pipeline['id'][:8]}")

print(f"\nUsing pipeline: {cycle47_pipeline['id']}")
print(f"  Type: {cycle47_pipeline.get('pipeline_type')}")
print(f"  Phase: {cycle47_pipeline.get('current_phase')}")
print(f"  Project: {cycle47_pipeline.get('project_id')}")

# 2. Try to advance the pipeline
print("\n=== Advancing pipeline through phases ===")
for phase in ["idea", "requirements", "design", "implementation", "testing", "deploy"]:
    r = fetch(f"/pipelines/{cycle47_pipeline['id']}/advance", method="POST",
              data=json.dumps({"to_phase": phase}).encode())
    if r:
        print(f"  Advance to {phase}: {r.get('current_phase', '?')}")
    else:
        print(f"  Advance to {phase}: failed")
        break

# 3. Check cycle #47 idea status
print("\n=== Cycle 47 status ===")
ideas = fetch("/ideas/")
for i in ideas:
    if '47' in i.get('title',''):
        print(f"  [{i['id'][:8]}] {i['title']} status={i['status']}")

# 4. Check cycle #48 idea
print("\n=== Cycle 48 status ===")
for i in ideas:
    if '48' in i.get('title',''):
        print(f"  [{i['id'][:8]}] {i['title']} status={i['status']}")
        # Try to start it
        r = fetch(f"/ideas/{i['id']}/start", method="POST", data=json.dumps({}).encode())
        if r:
            print(f"  Start result: status={r.get('idea',{}).get('status','?')}")
        else:
            print(f"  Start failed")

# 5. Check overall state
print("\n=== Final state ===")
tasks = fetch("/tasks/")
if tasks:
    active_tasks = [t for t in tasks if t.get('status') in ('pending','in_progress','todo')]
    print(f"Active tasks: {len(active_tasks)}")
    for t in active_tasks[:5]:
        print(f"  [{t.get('priority','?')}] {t['title'][:60]} ({t.get('status','?')})")

pipelines = fetch("/pipelines/")
active_p = [p for p in pipelines if p.get('current_phase') != 'done']
print(f"Active pipelines: {len(active_p)}")
