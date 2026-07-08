import json, sys, urllib.request
from collections import Counter

# Check ideas
resp = urllib.request.urlopen("http://127.0.0.1:8765/api/ideas/")
ideas = json.loads(resp.read())
not_done = [i for i in ideas if i.get("status") != "done"]
print("=== IDEAS ===")
print(f"Total: {len(ideas)}, Not done: {len(not_done)}")
for i in not_done:
    print(f"  [{i.get('status')}] {i.get('title')} ({i.get('id')[:8]})")
ideas.sort(key=lambda x: x.get("created_at", ""))
print(f"Newest: [{ideas[-1].get('status')}] {ideas[-1].get('title')}")

# Check tasks
resp = urllib.request.urlopen("http://127.0.0.1:8765/api/tasks/")
tasks = json.loads(resp.read())
active = [t for t in tasks if t.get("status") not in ("done", "cancelled")]
print("\n=== TASKS ===")
print(f"Total: {len(tasks)}, Active: {len(active)}")
statuses = Counter(t.get("status") for t in tasks)
for s, c in statuses.most_common():
    print(f"  {s}: {c}")

# Check pipelines
resp = urllib.request.urlopen("http://127.0.0.1:8765/api/pipelines/")
data = json.loads(resp.read())
ps = data if isinstance(data, list) else [data]
phases = Counter(p.get("current_phase", "?") for p in ps)
print("\n=== PIPELINES ===")
print(f"Total: {len(ps)}")
for ph, c in sorted(phases.items()):
    print(f"  {ph}: {c}")

# Health check
resp = urllib.request.urlopen("http://127.0.0.1:8765/health")
health = json.loads(resp.read())
print(f"\n=== HEALTH ===")
print(f"Status: {health.get('status')}, Version: {health.get('version')}")
