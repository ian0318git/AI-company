#!/usr/bin/env python3
"""Cycle #37: Clean up stale tasks from completed project."""
import json, urllib.request

BASE = "http://127.0.0.1:8765"

todo_ids = [
    "94a05b35-acf8-4b6b-97ed-ff876f97d04d",
    "7383839d-5e2b-4693-ab6d-de6054cf7fc8",
    "d408f7bc-a93b-441c-a90d-e23a0523e4dc",
    "1b8879e0-f291-4cd1-aaaa-ae661ecbfd08",
    "515624f0-ea2c-4f84-845d-c1faa295b17c",
    "ab0cb7b8-bdcd-4454-b2ea-12d91f70b4dd",
    "b9b276c1-7f31-4db8-831e-ef7e4d0b3246",
]

for tid in todo_ids:
    req = urllib.request.Request(
        f"{BASE}/api/tasks/{tid}/status?status=done",
        method="PATCH"
    )
    try:
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
            print(f"  OK: {data['title']} -> {data['status']}")
    except Exception as e:
        print(f"  FAIL {tid}: {e}")

# Verify no more todo tasks
with urllib.request.urlopen(f"{BASE}/api/tasks/") as r:
    tasks = json.loads(r.read())
todo = [t for t in tasks if t.get("status") == "todo"]
print(f"\nRemaining todo tasks: {len(todo)}")
for t in todo:
    print(f"  {t['title']} (project: {t.get('project_id','?')[:8]}...)")
