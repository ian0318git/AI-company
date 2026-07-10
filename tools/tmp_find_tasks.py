"""Find tasks for the evolution pipeline."""
import json, urllib.request

resp = urllib.request.urlopen('http://127.0.0.1:8765/api/tasks/?limit=300')
data = json.loads(resp.read())

# The pipeline was created from idea 7da62dfd
# Look for tasks without project_id (or with pipeline-related project_id)
# Also check what project_id the start endpoint assigned
pipeline_id = 'ce81d72f-db80-4adb-90a5-aad1dd528647'

for t in data['items']:
    pid = t.get('project_id', '') or ''
    if pid.endswith(pipeline_id[:8]) or pipeline_id[:12] in pid:
        print(f"  MATCH: [{t['status']}] {t['title']} proj={pid[:20]} created={t.get('created_at','')[-8:]}")
    if t.get('created_at','') > '2026-07-10T00:20':
        print(f"  RECENT: [{t['status']}] {t['title']} proj={pid[:20]} agent={t.get('assigned_agent','?')}")

# Also look for the idea to get its project_id
resp = urllib.request.urlopen('http://127.0.0.1:8765/api/ideas/7da62dfd-336a-4118-8afc-c41dda588702')
idea = json.loads(resp.read())
print(f"\nIdea project_id from start: looking for project linked to this idea...")

# Check projects
resp = urllib.request.urlopen('http://127.0.0.1:8765/api/projects/?limit=50')
proj_data = json.loads(resp.read())
for p in proj_data['items']:
    created = p.get('created_at', '')
    if '2026-07-10' in created:
        print(f"  PROJECT: [{p.get('status','?')}] {p.get('name','?')[:50]} id={p.get('id','-')[:12]} created={created}")

# Also check what groups the tasks into pipelines
# The start endpoint returned tasks with specific IDs - check if they exist
task_ids = [
    "2cc4b1e5-be7a-4628-aa4e-941de3fcabd1",
    "8de164a6-4276-408b-b37b-5e74223a6427",
    "3e14ae2d-d737-45e1-9faa-3b8ab4380a12",
    "33de52a5-2b57-4a6b-a8b1-9fefc7eeefc8",
    "9176e170-33e0-4b05-9d73-b3e6de185e1c",
    "8608158a-e9b2-4225-85a8-7c72106a878a",
    "e4822993-76d5-44a3-987d-e0f062ee33a3",
    "94a608ac-0d9d-4440-903f-282933d1434b",
]
existing = [t for t in data['items'] if t['id'] in task_ids]
print(f"\nExpected tasks found: {len(existing)}/{len(task_ids)}")
for t in existing:
    print(f"  [{t['status']}] {t['title'][:50]} proj={t.get('project_id','-')[:12]}")
missing = [i for i in task_ids if i not in {t['id'] for t in data['items']}]
if missing:
    print(f"  Missing from full list: {len(missing)}")
