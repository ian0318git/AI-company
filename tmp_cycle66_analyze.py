#!/usr/bin/env python3
import json, sys

with open("/home/ian/.claude/projects/-home-ian-github-project-AI-company/03df68d2-273d-403b-a232-781af0a10970/tool-results/blhn01tnj.txt") as f:
    tasks = json.load(f)

pending = [t for t in tasks if t.get('status') in ('pending', 'in_progress', 'paused')]
pending.sort(key=lambda t: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(t.get('priority','medium'), 99))

print(f"Total tasks: {len(tasks)}")
print(f"Pending tasks: {len(pending)}")
print()
for t in pending:
    print(f"  [{t['status']:12s}] priority={t.get('priority','?'):8s} id={t['id'][:8]}... {t['title']}")
    if t.get('description'):
        print(f"       desc: {t['description'][:100]}")
    if t.get('project_id'):
        print(f"       project_id: {t['project_id']}")
    print()
