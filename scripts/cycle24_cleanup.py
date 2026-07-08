#!/usr/bin/env python3
"""Clean up remaining cycle #23 tasks and complete all pending items."""
import json, urllib.request

# Step 1: Complete cycle #23 project (need to send full body with name)
req = urllib.request.Request(
    "http://127.0.0.1:8765/api/projects/5b7f4253-54bc-4881-b6f1-c68245439b7f",
    data=json.dumps({
        "name": "Idle cycle #23 — auto-system health check",
        "status": "completed"
    }).encode(),
    headers={"Content-Type": "application/json"},
    method="PATCH"
)
try:
    with urllib.request.urlopen(req) as resp:
        r = json.loads(resp.read())
        print(f"Cycle #23: {r.get('status')}")
except urllib.error.HTTPError as e:
    print(f"Cycle #23 update error: {e.code} {e.read().decode()[:300]}")

# Step 2: Start the cycle #23 idea if it's still new
req = urllib.request.Request("http://127.0.0.1:8765/api/ideas/688591b8-19c1-44cf-87d1-55bc0dfe09a7")
with urllib.request.urlopen(req) as resp:
    idea = json.loads(resp.read())
    print(f"Idea #23 status: {idea.get('status')}")

if idea.get("status") == "new":
    # Refine it first
    req = urllib.request.Request(
        "http://127.0.0.1:8765/api/ideas/688591b8-19c1-44cf-87d1-55bc0dfe09a7/refine",
        data=json.dumps({
            "refined_description": "Autonomous cycle #23 health check completed. All pipelines done, server healthy.",
            "suggested_pipeline": "quick-prototype"
        }).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"Refined: {json.loads(resp.read()).get('status')}")
    except urllib.error.HTTPError as e:
        print(f"Refine error: {e.code}")

    # Start it
    req = urllib.request.Request(
        "http://127.0.0.1:8765/api/ideas/688591b8-19c1-44cf-87d1-55bc0dfe09a7/start",
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            r = json.loads(resp.read())
            print(f"Started: idea={r['idea'].get('status')}, pipeline={r['pipeline'].get('id', '?')[:8]}...")
    except urllib.error.HTTPError as e:
        print(f"Start error: {e.code} {e.read().decode()[:200]}")
