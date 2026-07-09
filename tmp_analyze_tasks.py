import json, sys
data = json.load(sys.stdin)
statuses = set(t.get("status") for t in data)
print("Statuses:", statuses)
for s in sorted(statuses):
    count = sum(1 for t in data if t.get("status") == s)
    print(f"  {s}: {count}")
print()
for t in data:
    s = t.get("status")
    if s != "done":
        print(f"  [{s}] {t.get('title')} (p={t.get('priority')})")
