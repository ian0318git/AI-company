#!/usr/bin/env python3
"""Finish cycle #24: mark cycle #23 as completed, run final status check."""
import json, urllib.request

# Step 1: Complete cycle #23 project
req = urllib.request.Request(
    "http://127.0.0.1:8765/api/projects/5b7f4253-54bc-4881-b6f1-c68245439b7f",
    data=json.dumps({"status": "completed"}).encode(),
    headers={"Content-Type": "application/json"},
    method="PATCH"
)
try:
    with urllib.request.urlopen(req) as resp:
        r = json.loads(resp.read())
        print(f"Cycle #23: {r.get('status')}")
except urllib.error.HTTPError as e:
    print(f"Cycle #23 update error: {e.code} {e.read().decode()[:200]}")

# Step 2: Run final health check
import urllib.request
for endpoint in ["/health", "/api/ideas/", "/api/tasks/", "/api/projects/", "/api/pipelines/"]:
    try:
        req = urllib.request.Request(f"http://127.0.0.1:8765{endpoint}")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            if isinstance(data, list):
                print(f"  {endpoint}: {len(data)} items - OK")
            elif isinstance(data, dict):
                s = data.get("status", data.get("detail", "OK"))
                print(f"  {endpoint}: status={s} - OK")
    except urllib.error.HTTPError as e:
        print(f"  {endpoint}: HTTP {e.code}")
    except Exception as e:
        print(f"  {endpoint}: {e}")

# Step 3: Count ideas by status
req = urllib.request.Request("http://127.0.0.1:8765/api/ideas/")
with urllib.request.urlopen(req) as resp:
    ideas = json.loads(resp.read())
    status_counts = {}
    for i in ideas:
        s = i.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1
    print(f"\nIdeas by status: {json.dumps(status_counts)}")

# Step 4: Count tasks by status
req = urllib.request.Request("http://127.0.0.1:8765/api/tasks/")
with urllib.request.urlopen(req) as resp:
    tasks = json.loads(resp.read())
    status_counts = {}
    for t in tasks:
        s = t.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1
    print(f"Tasks by status: {json.dumps(status_counts)}")

# Step 5: Count projects by status
req = urllib.request.Request("http://127.0.0.1:8765/api/projects/")
with urllib.request.urlopen(req) as resp:
    projects = json.loads(resp.read())
    status_counts = {}
    for p in projects:
        s = p.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1
    print(f"Projects by status: {json.dumps(status_counts)}")
