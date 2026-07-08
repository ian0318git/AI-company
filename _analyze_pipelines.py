import json, sys
data = json.load(sys.stdin)
ps = data if isinstance(data, list) else [data]
active = [p for p in ps if p.get("status") not in ("completed", "failed", "cancelled")]
done = [p for p in ps if p.get("status") == "completed"]
print(f"Total: {len(ps)}, Active: {len(active)}, Completed: {len(done)}")
for p in active:
    print(f"  [{p.get('status','?')}] id={str(p.get('id','?'))[:16]} type={p.get('type','?')}")
for p in done[-3:]:
    print(f"  [done] id={str(p.get('id','?'))[:16]} type={p.get('type','?')} idea={str(p.get('idea_id','?'))[:8]}")
