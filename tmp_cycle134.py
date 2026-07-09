import json

with open('/home/ian/github-project/AI-company/tmp_tasks_134.json') as f:
    tasks = json.load(f)

statuses = {}
for t in tasks:
    s = t.get('status', 'unknown')
    statuses[s] = statuses.get(s, 0) + 1
print('Status counts:', json.dumps(statuses, indent=2))

active = [t for t in tasks if t.get('status') in ('pending', 'todo', 'ready', 'queued')]
print(f'Active tasks: {len(active)}')
for t in active:
    print(f'  - {t["id"]}: {t["title"]} (p={t.get("priority","?")})')

inp = [t for t in tasks if t.get('status') in ('in_progress', 'running')]
print(f'In-progress tasks: {len(inp)}')
for t in inp:
    print(f'  - {t["id"]}: {t["title"]}')

sorted_t = sorted(tasks, key=lambda t: t.get('updated_at', ''), reverse=True)
print('Latest 10 tasks:')
for t in sorted_t[:10]:
    print(f'  [{t["status"]}] {t["id"][:8]}... {t["title"]} (p={t.get("priority","?")})')

done = [t for t in tasks if t.get('status') == 'done']
print(f'Done tasks: {len(done)}')
