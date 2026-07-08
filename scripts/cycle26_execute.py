"""Execute cycle 26 - complete high-priority task and advance pipeline."""
import json, urllib.request

BASE = "http://127.0.0.1:8765"

def patch(url):
    req = urllib.request.Request(url, method="PATCH")
    return json.loads(urllib.request.urlopen(req).read())

def post(url, data=None):
    req = urllib.request.Request(url, method="POST")
    if data:
        req.data = json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    return json.loads(urllib.request.urlopen(req).read())

# Step 1: Mark high-priority task as done
print("Completing: Define research questions and scope boundaries")
result = patch(f"{BASE}/api/tasks/38184b60-8d02-4b02-abe8-981e5cc5ee7e/status?status=done")
print(f"  Status: {result.get('status')}")

# Step 2: Advance pipeline from requirements to next phase
print("\nAdvancing pipeline 73060985...")
result = post(f"{BASE}/api/pipelines/73060985-0543-45e9-ba46-316da3c223b7/advance", {})
print(f"  Phase: {result.get('current_phase')}")

# Step 3: Start the next high-priority task - Identify academic databases
print("\nStarting: Identify academic databases and data sources")
result = patch(f"{BASE}/api/tasks/6fb8385d-7e24-4c34-9bda-2f5edee5921e/status?status=in_progress")
print(f"  Status: {result.get('status')}")
