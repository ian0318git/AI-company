import json, sys
tasks = json.load(sys.stdin)
# Check what cycle #1 did with its project
cycle1_tasks = [t for t in tasks if t.get("project_id") == "58036850-f955-4cac-8f8d-3db4ab4b266e" and t.get("status") == "todo"]
cycle2_tasks = [t for t in tasks if t.get("project_id") == "dd898219-f146-4cf1-83cd-38f9988d4b3d" and t.get("status") == "todo"]
print(f"M5Stack project (58036850) stale todo tasks: {len(cycle1_tasks)}")
for t in cycle1_tasks:
    print(f"  [{t.get('priority')}] {t['title']} id={t['id'][:8]}")
print(f"\nCycle #1 project (dd898219) stale todo tasks: {len(cycle2_tasks)}")
for t in cycle2_tasks:
    print(f"  [{t.get('priority')}] {t['title']} id={t['id'][:8]}")
print(f"\nAll task statuses:")
from collections import Counter
statuses = Counter(t.get("status") for t in tasks)
for s, c in statuses.most_common():
    print(f"  {s}: {c}")
