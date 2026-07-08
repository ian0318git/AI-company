"""Mark orphaned tasks done via correct PATCH /status endpoint."""
import json, urllib.request, urllib.error

task_ids = [
    "7bd1ccc2-f85d-46a0-ade3-e96ebb23057d",
    "603a68d1-f66a-4918-a95c-a6d1026b1e27",
    "274e55d3-b32f-451c-b353-b8057b5edfd3",
    "5ee95f46-b4fa-48bb-a854-f245070a5da3",
]

BASE = "http://127.0.0.1:8765/api"

for tid in task_ids:
    data = json.dumps({"status": "done"}).encode()
    req = urllib.request.Request(
        f"{BASE}/tasks/{tid}/status",
        data=data,
        headers={"Content-Type": "application/json"},
        method="PATCH"
    )
    try:
        resp = urllib.request.urlopen(req)
        d = json.load(resp)
        print(f"{tid[:8]}... -> {d.get('status', '?')}")
    except urllib.error.HTTPError as e:
        print(f"{tid[:8]}... -> ERROR {e.code}: {e.read().decode()[:100]}")

# Verify
resp = urllib.request.urlopen(f"{BASE}/tasks/")
tasks = json.load(resp)
pending = [t for t in tasks if t['status'] != 'done']
print(f"\nRemaining pending: {len(pending)}")
