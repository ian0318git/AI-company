#!/usr/bin/env python3
import json, subprocess, sys
result = subprocess.run(['curl', '-s', 'http://127.0.0.1:8765/api/tasks/'], capture_output=True, text=True)
tasks = json.loads(result.stdout)
proj_tasks = [t for t in tasks if t.get('project_id') == '232eaf58-19bf-49c4-ba53-dce56b908c80']
print("Project 232eaf58 tasks:")
prio = {'high':0, 'medium':1, 'low':2}
for t in sorted(proj_tasks, key=lambda x: prio.get(x.get('priority','medium'),1)):
    print("  [%s] %s (p:%s)" % (t['status'], t['title'], t.get('priority','?')))
print()

# Also show pipelines for this project
result2 = subprocess.run(['curl', '-s', 'http://127.0.0.1:8765/api/pipelines/'], capture_output=True, text=True)
pipes = json.loads(result2.stdout)
for p in pipes:
    if p.get('project_id') == '232eaf58-19bf-49c4-ba53-dce56b908c80':
        print("Pipeline %s: phase=%s" % (p['id'][:12], p['current_phase']))
