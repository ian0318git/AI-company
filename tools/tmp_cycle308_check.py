#!/usr/bin/env python3
"""Check cycle 308 pipeline status."""
import json, urllib.request, sys

BASE = "http://127.0.0.1:8765/api"

def api(method, path, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

# Check the idea
idea = api("GET", "/ideas/15d6ed45-de4d-4e78-83d1-a7003ddd3b1b")
print("=== Idea ===")
for k in ("id", "title", "status", "project_id", "suggested_pipeline"):
    print(f"  {k}: {idea.get(k)}")

# Try starting the pipeline again
print("\n=== Restarting pipeline ===")
start = api("POST", "/ideas/15d6ed45-de4d-4e78-83d1-a7003ddd3b1b/start", {})
if start:
    print(json.dumps(start, indent=2, default=str))
else:
    print("start returned None")

# List current pipelines to find new ones
print("\n=== Recent pipelines ===")
pipes = api("GET", "/pipelines/")
for p in pipes[-3:]:
    print(json.dumps(p, indent=2, default=str))
