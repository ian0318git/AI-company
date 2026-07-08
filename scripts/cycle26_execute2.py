"""Execute cycle 26 - complete task 2, start task 3."""
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

# Complete task: Identify academic databases and data sources
print("Completing: Identify academic databases and data sources")
result = patch(f"{BASE}/api/tasks/6fb8385d-7e24-4c34-9bda-2f5edee5921e/status?status=done")
print(f"  Status: {result.get('status')}")

# Advance pipeline from design to implementation
print("\nAdvancing pipeline 73060985...")
result = post(f"{BASE}/api/pipelines/73060985-0543-45e9-ba46-316da3c223b7/advance", {})
print(f"  Phase: {result.get('current_phase')}")

# Start task: Draft report outline and structure
print("\nStarting: Draft report outline and structure")
result = patch(f"{BASE}/api/tasks/033fc8ff-6dd6-48ac-93d1-0aa867c584f2/status?status=in_progress")
print(f"  Status: {result.get('status')}")
