"""Mark tasks in_progress with correct API."""
import json, urllib.request, urllib.error

BASE = "http://127.0.0.1:8765"

def fetch(method, path, data=None):
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "detail": e.read().decode()[:500]}

# Mark tasks - status is a query parameter
tasks = fetch("GET", "/api/tasks/")
todo_tasks = [t for t in tasks if t.get("project_id","").startswith("ae54db64") and t.get("status") == "todo"]

for i, t in enumerate(todo_tasks[:3]):
    tid = t["id"]
    url = f"{BASE}/api/tasks/{tid}/status?status=in_progress"
    req = urllib.request.Request(url, method="PATCH")
    try:
        with urllib.request.urlopen(req) as r:
            result = json.loads(r.read())
        print(f"[{i+1}/3] {t['title'][:60]}")
        print(f"       -> id={result.get('id','?')[:12]}... status={result.get('status','?')}")
    except urllib.error.HTTPError as e:
        print(f"[{i+1}/3] ERROR: {e.code} - {e.read().decode()[:200]}")
