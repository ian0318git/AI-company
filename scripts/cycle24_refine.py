#!/usr/bin/env python3
"""Refine the cycle #24 idea and advance the idle cycle #23 pipeline."""
import json, urllib.request, sys

IDEA_ID = sys.argv[1]

# Step 1: Refine the idea
req = urllib.request.Request(
    f'http://127.0.0.1:8765/api/ideas/{IDEA_ID}/refine',
    data=json.dumps({
        "refined_description": "System idle cycle #24: all 25 pipelines completed, no pending tasks, server healthy. Reporting idle state.",
        "suggested_pipeline": "quick-prototype"
    }).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
try:
    with urllib.request.urlopen(req) as resp:
        print("Refine OK:", resp.status, json.loads(resp.read()))
except urllib.error.HTTPError as e:
    print("Refine error:", e.code, e.read().decode())
    sys.exit(1)

# Step 2: Start the idea (creates pipeline)
req = urllib.request.Request(
    f'http://127.0.0.1:8765/api/ideas/{IDEA_ID}/start',
    method='POST'
)
try:
    with urllib.request.urlopen(req) as resp:
        print("Start OK:", resp.status, json.loads(resp.read()))
except urllib.error.HTTPError as e:
    print("Start error:", e.code, e.read().decode())
    if "already" not in str(e.read()):
        sys.exit(1)
