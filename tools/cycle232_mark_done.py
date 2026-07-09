"""Mark orphan tasks as 'done' since their parent projects are already completed."""
from urllib.request import Request, urlopen
from urllib.error import URLError
import json

API = "http://127.0.0.1:8765"

# Get all todo tasks
with urlopen(f"{API}/api/tasks/") as r:
    tasks = json.loads(r.read().decode())

todo_ids = [t for t in tasks if t["status"] == "todo"]
print(f"Found {len(todo_ids)} orphan tasks to mark as done.")

for t in todo_ids:
    tid = t["id"]
    title = t["title"]
    req = Request(f"{API}/api/tasks/{tid}/status?status=done", method="PATCH")
    try:
        with urlopen(req) as r:
            d = json.loads(r.read().decode())
            print(f"  [{d['status']}] {title[:55]}")
    except URLError as e:
        print(f"  FAIL: {tid[:12]} {title[:30]} -> {e}")
