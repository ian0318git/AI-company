"""Upload a deliverable file to an idea via the API."""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

idea_id = sys.argv[1]
file_path = sys.argv[2]

with open(file_path, "rb") as f:
    content = base64.b64encode(f.read()).decode()

filename = os.path.basename(file_path)
payload = json.dumps({"filename": filename, "content": content, "encoding": "base64"}).encode()

req = urllib.request.Request(
    f"http://127.0.0.1:8765/api/ideas/{idea_id}/deliverables",
    data=payload,
    method="POST",
    headers={"Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(req) as resp:
        print(json.dumps(json.loads(resp.read()), indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()}")
    sys.exit(1)
