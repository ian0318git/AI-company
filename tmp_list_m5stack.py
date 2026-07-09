#!/usr/bin/env python3
"""Fetch M5Stack project tasks with their IDs."""
import json, subprocess
r = subprocess.run(['curl', '-s', 'http://127.0.0.1:8765/api/tasks/'], capture_output=True, text=True)
tasks = json.loads(r.stdout)
proj_tasks = [t for t in tasks if t.get('project_id') == '232eaf58-19bf-49c4-ba53-dce56b908c80']
for t in sorted(proj_tasks, key=lambda x: x.get('created_at','')):
    print("id=%s  status=%s  title=%s" % (t['id'], t['status'], t['title']))
