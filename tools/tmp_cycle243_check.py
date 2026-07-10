"""Cycle #243 — check ideas and tasks."""
import json, urllib.request, sys

# Check ideas
resp = urllib.request.urlopen('http://127.0.0.1:8765/api/ideas/?limit=50')
data = json.loads(resp.read())
print("=== IDEAS ===")
print(f"Total: {data['total']}")
pending = [i for i in data['items'] if i['status'] in ('pending','new','draft')]
if pending:
    for i in pending:
        print(f"  NEW: [{i['status']}] {i['title']} (id: {i['id'][:8]})")
else:
    print("  No new/pending ideas to refine.")
# Also anything interesting
neut = [i for i in data['items'] if i['status'] not in ('done','archived')]
print(f"  Non-terminal status: {len(neut)}")
for i in neut:
    print(f"    [{i['status']}] {i['title']} pipe:{i.get('suggested_pipeline','?')}")

# Check tasks
resp = urllib.request.urlopen('http://127.0.0.1:8765/api/tasks/?limit=200')
data = json.loads(resp.read())
print("\n=== TASKS ===")
print(f"Total: {data['total']}")
todo = [t for t in data['items'] if t['status'] in ('todo','in_progress')]
print(f"Active (todo/in_progress): {len(todo)}")
if todo:
    for t in sorted(todo, key=lambda x: {'high':0,'medium':1,'low':2}.get(x.get('priority','medium'),1)):
        print(f"  [{t['status']}] p:{t.get('priority','?')} {t['title']}")
        print(f"    id:{t['id']}  proj:{t.get('project_id','-')}")
else:
    print("  None found.")
# Check for high/medium todo tasks specifically
high_todo = [t for t in data['items'] if t['status'] == 'todo' and t.get('priority') == 'high']
print(f"  High-priority todo: {len(high_todo)}")
for t in high_todo:
    print(f"    {t['title']} id:{t['id'][:8]}")

# Check projects
resp = urllib.request.urlopen('http://127.0.0.1:8765/api/projects/?limit=50')
data = json.loads(resp.read())
print("\n=== PROJECTS ===")
print(f"Total: {data['total']}")
active = [p for p in data['items'] if p.get('status') not in ('done','completed','archived')]
print(f"Active projects: {len(active)}")
for p in active:
    print(f"  [{p.get('status','?')}] {p.get('name','?')} (id:{p.get('id','-')[:8]})")
