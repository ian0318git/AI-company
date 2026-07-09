#!/usr/bin/env python3
import json, subprocess
# Find project for the real-time tracking idea
r = subprocess.run(['curl', '-s', 'http://127.0.0.1:8765/api/projects/'], capture_output=True, text=True)
try:
    projects = json.loads(r.stdout)
    for p in projects:
        if '追蹤' in p.get('name','') or '即時' in p.get('name','') or 'test' in p.get('name','').lower():
            print("Project id=%s name=%s status=%s" % (p['id'], p['name'], p['status']))
except:
    print("No projects or parse error")
    print(r.stdout[:200])

r2 = subprocess.run(['curl', '-s', 'http://127.0.0.1:8765/api/pipelines/'], capture_output=True, text=True)
pipes = json.loads(r2.stdout)
print("\nNon-done pipelines:")
for p in sorted(pipes, key=lambda x: x['created_at']):
    if p['current_phase'] not in ('done',):
        print("  [%s] type=%s id=%s proj=%s" % (p['current_phase'], p['pipeline_type'], p['id'][:12], p['project_id'][:12]))
