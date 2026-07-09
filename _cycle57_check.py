import json, sys
tasks = json.load(sys.stdin)
active = [t for t in tasks if t.get("status") in ("pending", "in_progress", "paused")]
print(f"{len(active)} active tasks:")
for t in active:
    p = t.get("priority") or "none"
    a = t.get("assigned_agent") or "unassigned"
    d = (t.get("description") or "")[:80]
    print(f"  {t['id'][:8]} | {t['status']:12} | pri={p:8} | agent={a:12} | {t['title']}")
    if d:
        print(f"  {'':14} desc: {d}")
