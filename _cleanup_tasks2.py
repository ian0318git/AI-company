import json, urllib.request

# Fetch tasks
resp = urllib.request.urlopen("http://127.0.0.1:8765/api/tasks/")
tasks = json.loads(resp.read())

# Find all todo tasks
todo = [t for t in tasks if t.get("status") == "todo"]
print(f"Stale todo tasks to clean: {len(todo)}")

for t in todo:
    tid = t["id"]
    title = t["title"]
    pid = t.get("project_id", "?")[:16]
    url = f"http://127.0.0.1:8765/api/tasks/{tid}/status?status=done"
    try:
        req = urllib.request.Request(url, method="PATCH")
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        print(f"  [OK] {title} (proj={pid}) -> {result.get('status')}")
    except Exception as e:
        print(f"  [FAIL] {title} - {e}")
