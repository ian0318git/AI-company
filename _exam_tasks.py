import json, sys
tasks = json.load(sys.stdin)
# Find the high priority task
high = [t for t in tasks if t.get("priority") == "high"]
for t in high:
    print(f"High-priority task:")
    print(f"  Title: {t.get('title')}")
    print(f"  Description: {t.get('description')}")
    print(f"  Project ID: {t.get('project_id')}")
    print(f"  Status: {t.get('status')}")
    print(f"  Parent task: {t.get('parent_task_id')}")
    print(f"  Created: {t.get('created_at')}")

# Check all active task project_ids
todo = [t for t in tasks if t.get("status") == "todo"]
projects = set()
for t in todo:
    pid = t.get("project_id", "?")
    projects.add(pid)
print(f"\nActive todo tasks: {len(todo)}")
print(f"Unique project IDs: {len(projects)}")
for pid in sorted(projects):
    ptasks = [t for t in todo if t.get("project_id") == pid]
    print(f"  Project {pid[:16]}: {len(ptasks)} tasks")
    for t in ptasks:
        print(f"    [{t.get('priority')}] {t['title']}")
