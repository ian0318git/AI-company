import json, sys, urllib.request, urllib.parse

tasks = json.load(sys.stdin)
# Find all todo tasks in completed projects
todo = [t for t in tasks if t.get("status") == "todo"]
print(f"Stale todo tasks to clean: {len(todo)}")
for t in todo:
    tid = t["id"]
    title = t["title"]
    url = f"http://127.0.0.1:8765/api/tasks/{tid}/status?status=done"
    try:
        req = urllib.request.Request(url, method="PATCH")
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        print(f"  OK: {title} -> {result.get('status')}")
    except Exception as e:
        print(f"  FAIL: {title} - {e}")
