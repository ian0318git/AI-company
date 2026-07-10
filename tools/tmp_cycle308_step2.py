#!/usr/bin/env python3
"""Advance stuck pipelines, then fix pipeline-type keyword matching."""
import json, urllib.request, urllib.error, sys, time

BASE = "http://127.0.0.1:8765/api"

def api(method, path, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  API error {e.code}: {err[:150]}", file=sys.stderr)
        return None

# Step 1: Advance both stuck pipelines
print("=== Step 1: Advance stuck pipelines ===")
pipe_ids = [
    "7844f653-10fb-4dc7-a73b-abf17e7b4c5a",
    "4ef45bd2-e6a2-4fe3-a2d8-0b99b8c1f429",
]
for pid in pipe_ids:
    for i in range(8):
        r = api("POST", f"/pipelines/{pid}/advance", {})
        if r:
            cp = r.get("current_phase") or (r.get("pipeline") or {}).get("current_phase", "?")
            print(f"  {pid[:12]} -> {cp}")
            if cp == "done":
                break
        else:
            print(f"  {pid[:12]} stuck at advance attempt {i}")
            break
        time.sleep(0.2)

# Step 2: Find the pipeline template matching logic in source
import os
SRC = "/home/ian/github-project/AI-company/src/ai_embedded_company"
print("\n=== Step 2: Find pipeline-type matching code ===")
matches = []
for root, dirs, files in os.walk(SRC):
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            try:
                with open(path) as fh:
                    content = fh.read()
                    if "pipeline" in content.lower() and ("keyword" in content.lower() or "suggest" in content.lower() or "match" in content.lower()):
                        matches.append((path, len(content)))
            except:
                pass
matches.sort(key=lambda x: -x[1])
for path, sz in matches[:10]:
    rel = os.path.relpath(path, SRC)
    print(f"  {rel} ({sz} bytes)")

# Step 3: Check final pipeline state
print("\n=== Step 3: Final state ===")
pipes = api("GET", "/pipelines/")
stuck = [p for p in pipes if p["current_phase"] != "done"]
print(f"Stuck pipelines remaining: {len(stuck)}")
for p in stuck:
    print(f"  {p['id'][:12]} phase={p['current_phase']} type={p['pipeline_type']}")

# Check the idea state
ideas = api("GET", "/ideas/")
for i in ideas.get("items", []):
    if i["status"] not in ("done", "archived"):
        print(f"Active idea: {i['status']} | {i['title'][:60]}")
