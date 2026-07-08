"""Final check for cycle 26."""
import json, urllib.request

BASE = "http://127.0.0.1:8765"

# Check ideas
data = json.loads(urllib.request.urlopen(f"{BASE}/api/ideas/").read())
for i in data:
    print(f"  Idea: [{i.get('status')}] {i['title'][:60]}")

print()

# Check pipeline for evolution project
pipelines = json.loads(urllib.request.urlopen(f"{BASE}/api/pipelines/").read())
for p in pipelines:
    if p.get("project_id","").startswith("0fda8d2e"):
        print(f"  Pipeline: type={p['pipeline_type']}, phase={p['current_phase']}")
        # Get detail
        detail = json.loads(urllib.request.urlopen(f"{BASE}/api/pipelines/{p['id']}").read())
        for s in detail.get("steps", []):
            print(f"    Step: [{s['status']}] {s['phase']}/{s['name']}")

print()

# Check task summary for evolution project
tasks = json.loads(urllib.request.urlopen(f"{BASE}/api/tasks/").read())
proj_tasks = [t for t in tasks if t.get("project_id","").startswith("0fda8d2e")]
print(f"Evolution project tasks: {len(proj_tasks)}")
for t in proj_tasks:
    print(f"  [{t['status']}] {t['title'][:55]} (pri={t['priority']})")

# Overall summary
from collections import Counter
c = Counter(t.get("status","?") for t in tasks)
print(f"\nOverall task summary: {dict(c)}")
