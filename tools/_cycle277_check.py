"""Cycle #277 status check - count ideas/projects/pipelines by status."""
import subprocess, json
from collections import Counter

# Count ideas
r = subprocess.run(['curl', '-s', 'http://127.0.0.1:8765/api/ideas/'], capture_output=True, text=True)
ideas = json.loads(r.stdout)
print("Ideas:", dict(Counter(i['status'] for i in ideas['items'])))

# Count projects
r = subprocess.run(['curl', '-s', 'http://127.0.0.1:8765/api/projects/'], capture_output=True, text=True)
projects = json.loads(r.stdout)
print("Projects:", dict(Counter(p['status'] for p in projects['items'])))

# Count tasks
r = subprocess.run(['curl', '-s', 'http://127.0.0.1:8765/api/tasks/'], capture_output=True, text=True)
tasks = json.loads(r.stdout)
print("Tasks:", dict(Counter(t['status'] for t in tasks['items'])))
print("Total tasks:", tasks['total'])
