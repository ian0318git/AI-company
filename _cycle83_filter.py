#!/usr/bin/env python3
import json, sys

tasks = json.load(sys.stdin)

# Filter tasks that are NOT done
pending = [t for t in tasks if t.get('status') not in ('done', 'completed')]
pending.sort(key=lambda t: {'high': 0, 'medium': 1, 'low': 2}.get(t.get('priority', 'medium'), 3))

print(f'Pending tasks count: {len(pending)}')
for t in pending:
    print(f'  [{t.get("priority","?"):>6}] {t["title"][:80]} (status={t["status"]}, id={t["id"]})')

# Also check pipeline states
print('\n--- Pipeline/project states ---')
projects_seen = set()
for t in tasks:
    pid = t.get('project_id')
    if pid and pid not in projects_seen:
        projects_seen.add(pid)
print(f'Unique project IDs referenced: {len(projects_seen)}')
