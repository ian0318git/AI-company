"""Auto-seed a maintenance idea for deep idle state."""
import json
import urllib.request
import urllib.error

SEED = {
    "title": "Dependency Version Audit",
    "raw_description": "Audit all Python and Node.js dependencies for updates, security advisories, and breaking changes. Generate upgrade plan.",
    "tags": ["autonomous-cycle", "auto-seed", "maintenance"],
    "suggested_pipeline": "research-spike",
}

url = "http://127.0.0.1:8765/api/ideas/"
data = json.dumps(SEED).encode()
req = urllib.request.Request(url, data=data, method="POST")
req.add_header("Content-Type", "application/json")

try:
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    print("CREATED: " + json.dumps(result, indent=2, ensure_ascii=False))
except urllib.error.HTTPError as e:
    print("HTTP " + str(e.code) + ": " + e.read().decode())
except Exception as e:
    print("ERROR: " + str(e))
