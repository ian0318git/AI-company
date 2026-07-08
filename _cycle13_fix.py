#!/usr/bin/env python3
"""Diagnose and fix cycle 13 operations."""
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

# Check what endpoints are available for ideas
print("=== Ideas endpoint available methods ===")
# GET the ideas list
ideas = fetch("/ideas/")
for i in ideas:
    if i['id'].startswith('7bf1bc73') or i['id'].startswith('058d258c'):
        print(f"Idea {i['id'][:8]}: {i['title']} status={i['status']}")

# Try refine on cycle 47 (already did this - it's refining)
print("\n=== Refining cycle #47 ===")
r = fetch(f"/ideas/7bf1bc73-28d6-4cee-b7fe-2e017ffc9516/refine", method="POST",
          data=json.dumps({"refined_description": "All 46 ideas done, 270 tasks done, 52 pipelines completed, 46 projects done. Server healthy. No new work. System idle."}).encode())
print(f"Refine result: {r}")

# Try start on cycle 47 (to move it forward)
print("\n=== Starting cycle #47 ===")
r = fetch(f"/ideas/7bf1bc73-28d6-4cee-b7fe-2e017ffc9516/start", method="POST", data=json.dumps({}).encode())
print(f"Start result: {r}")

# Try workflow endpoint
print("\n=== Workflow for cycle #47 ===")
r = fetch(f"/ideas/7bf1bc73-28d6-4cee-b7fe-2e017ffc9516/workflow", method="POST",
          data=json.dumps({"pipeline_type": "research-spike"}).encode())
print(f"Workflow result: {r}")

# Check new idea status
print("\n=== New idea #48 ===")
ideas = fetch("/ideas/")
for i in ideas:
    if i['id'].startswith('058d258c'):
        print(f"Idea {i['id'][:8]}: {i['title']} status={i['status']}")

# Try starting cycle #48
print("\n=== Starting cycle #48 ===")
r = fetch(f"/ideas/058d258c-a976-4445-af58-0e17cd03016e/start", method="POST", data=json.dumps({}).encode())
print(f"Start result: {r}")

# List all pipelines to see state
print("\n=== Pipeline status ===")
pipelines = fetch("/pipelines/")
print(f"Total pipelines: {len(pipelines)}")
