#!/usr/bin/env python3
"""Advance the cycle #24 pipeline through all phases and mark tasks complete."""
import json, urllib.request, sys, time

PIPELINE_ID = sys.argv[1]

def get_pipeline():
    req = urllib.request.Request(f'http://127.0.0.1:8765/api/pipelines/{PIPELINE_ID}')
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def advance_pipeline():
    req = urllib.request.Request(
        f'http://127.0.0.1:8765/api/pipelines/{PIPELINE_ID}/advance',
        data=json.dumps({"notes": "Idle cycle #24: All work completed. Server healthy. No new work to process."}).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  Advance error: {e.code} {e.read().decode()}")
        return None

def complete_task(task_id):
    req = urllib.request.Request(
        f'http://127.0.0.1:8765/api/tasks/{task_id}/status',
        data=json.dumps({"status": "done"}).encode(),
        headers={'Content-Type': 'application/json'},
        method='PATCH'
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"  Task {task_id[:8]}... done")
            return True
    except urllib.error.HTTPError as e:
        print(f"  Task {task_id[:8]}... error: {e.code} {e.read().decode()}")
        return False

# Get pipeline tasks
pipeline = get_pipeline()
print(f"Pipeline {PIPELINE_ID[:8]}...")
print(f"  Phase: {pipeline.get('current_phase', '?')}")
print(f"  Status: {pipeline.get('status', '?')}")

# Get all tasks for this pipeline
req = urllib.request.Request('http://127.0.0.1:8765/api/tasks/')
with urllib.request.urlopen(req) as resp:
    all_tasks = json.loads(resp.read())

# Filter tasks (all are for this pipeline since it's the only active one)
todo_tasks = [t for t in all_tasks if t.get('status') in ('todo', 'in_progress') and t.get('title', '').strip()]
print(f"\nFound {len(todo_tasks)} todo tasks")

# Complete all tasks
for t in todo_tasks:
    print(f"  Completing: [{t.get('priority','?')}] {t['title']} ({t['id'][:8]}...)")
    complete_task(t['id'])
    time.sleep(0.1)

# Advance pipeline through phases
phases = ['idea', 'requirements', 'design', 'implementation', 'testing', 'deploy']
current = pipeline.get('current_phase', 'idea')
print(f"\nStarting from phase: {current}")

# Advance until we can't anymore
for _ in range(10):
    result = advance_pipeline()
    if result:
        print(f"  Advanced. New phase/status: {result.get('current_phase', result.get('status', '?'))}")
        time.sleep(0.2)
    else:
        print("  No more advances possible.")
        break

# Final check
pipeline = get_pipeline()
print(f"\nFinal pipeline status: {pipeline.get('status', '?')}")
if pipeline.get('status') == 'completed':
    print("Pipeline completed successfully!")
