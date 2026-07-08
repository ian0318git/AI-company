import json, sys
tasks = json.load(sys.stdin)
active = [t for t in tasks if t.get("status") not in ("done", "cancelled")]
print(f"Active tasks: {len(active)}")
for t in active:
    print(f"  [{t['status']}] pri={t.get('priority','?')} {t['title']} id={t['id'][:8]}")
if not active:
    statuses = {}
    for t in tasks:
        s = t.get("status", "?")
        statuses[s] = statuses.get(s, 0) + 1
    print(f"Status breakdown: {statuses}")
    print(f"Total tasks: {len(tasks)}")
