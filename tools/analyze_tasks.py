import json, sys

tasks = json.load(sys.stdin)

print(f"Total tasks: {len(tasks)}")

status_counts = {}
for t in tasks:
    s = t["status"]
    status_counts[s] = status_counts.get(s, 0) + 1
print(f"By status: {json.dumps(status_counts, indent=2)}")

priority_counts = {}
for t in tasks:
    p = t["priority"]
    priority_counts[p] = priority_counts.get(p, 0) + 1
print(f"By priority: {json.dumps(priority_counts, indent=2)}")

non_done = [t for t in tasks if t["status"] not in ("done",)]
print(f"\nNon-done tasks ({len(non_done)}):")
for t in non_done:
    print(f"  [{t['status']}] priority={t['priority']} | {t['title']} | id={t['id']}")

# cross-tab: status x priority
from collections import defaultdict
cross = defaultdict(lambda: defaultdict(int))
for t in tasks:
    cross[t["status"]][t["priority"]] += 1
print(f"\nStatus x Priority cross-tab:")
for s in sorted(cross.keys()):
    print(f"  {s}: {dict(cross[s])}")
