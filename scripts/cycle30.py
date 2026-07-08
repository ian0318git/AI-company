"""Cycle #30 — idle cycle completion."""
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8765/api"

def api_get(path):
    resp = urllib.request.urlopen(f"{BASE}/{path}")
    return json.load(resp)

def api_post(path, data=None):
    body = json.dumps(data).encode() if data else b""
    req = urllib.request.Request(
        f"{BASE}/{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req)
        return json.load(resp)
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode()}

def api_patch(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{BASE}/{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="PATCH"
    )
    try:
        resp = urllib.request.urlopen(req)
        return json.load(resp)
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode()}

# Find idle cycle #30 idea
ideas = api_get("ideas/")
target = None
for i in ideas:
    if "Idle cycle #30" in i["title"]:
        target = i
        break

if not target:
    print("ERROR: Cycle30 idea not found")
    exit(1)

print(f"Found idea: {target['id'][:8]}... status={target['status']}")

# Start pipeline
result = api_post(f"ideas/{target['id']}/start")
print(f"Pipeline start: {json.dumps(result, indent=2)[:200]}")

# Get the pipeline ID
pipelines = api_get("pipelines/")
pipeline_id = None
for p in reversed(pipelines):
    if p["project_id"] == target["id"] or p["id"] not in [x["id"] for x in pipelines]:
        pipeline_id = p["id"]
        break

# Let's just list the most recent one
for p in reversed(pipelines):
    print(f"Pipeline: {p['id'][:8]}... phase={p['current_phase']} project={p['project_id'][:8]}...")
