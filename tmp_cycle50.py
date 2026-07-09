import json, sys, urllib.request

# Fetch ideas
with urllib.request.urlopen("http://127.0.0.1:8765/api/ideas/") as r:
    ideas = json.loads(r.read())
active = [i for i in ideas if i.get('status') not in ('done', 'archived')]
print("=== ACTIVE IDEAS ===")
if active:
    for i in active:
        print(f"[{i['status']}] {i['title']} (id={i['id'][:8]})")
else:
    print("No active ideas.")
statuses = set(i.get('status') for i in ideas)
print(f"Idea statuses: {statuses}")

# Fetch tasks
with urllib.request.urlopen("http://127.0.0.1:8765/api/tasks/") as r:
    tasks = json.loads(r.read())

# Find high-priority pending tasks
pending = [t for t in tasks if t.get('status') not in ('done',)]
print(f"\n=== NON-DONE TASKS ({len(pending)}) ===")
for t in pending:
    print(json.dumps(t, indent=2))
    print("---")

# Count by status
status_counts = {}
for t in tasks:
    s = t.get('status', 'unknown')
    status_counts[s] = status_counts.get(s, 0) + 1
print(f"Task status counts: {status_counts}")
