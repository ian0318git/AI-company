"""Final state check for Cycle 74 report."""
import json, urllib.request

BASE = "http://127.0.0.1:8765"

def fetch(path):
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return json.loads(r.read())

# Check Autonomous Idea Generator
idea = fetch("/api/ideas/6c54d738-080b-4783-9d81-a1239e714ebf")
print(f"Autonomous Idea Generator: status={idea.get('status')}, pipeline={idea.get('suggested_pipeline')}")

# Check Evolution Vaccine idea
ev_idea = fetch("/api/ideas/eff87aaf-f5df-466e-a508-5d1f1c232585")
print(f"Evolution Vaccine Injection: status={ev_idea.get('status')}")

# Check Prompt A/B Dashboard tasks
tasks = fetch("/api/tasks/")
ptasks = [t for t in tasks if t.get("project_id","").startswith("ae54db64")]
print(f"\nPrompt A/B Dashboard tasks:")
for t in ptasks:
    print(f"  [{t.get('status')}] {t.get('priority')} - {t.get('title','?')[:60]}")

# Find Autonomous Idea Generator pipeline
pipelines = fetch("/api/pipelines/")
# Find by project_id of the idea
new_pipes = [p for p in pipelines if p.get("project_id","").startswith("10c25577")]
print(f"\nAutonomous Idea Generator pipelines: {len(new_pipes)}")
for p in new_pipes:
    print(f"  phase={p.get('current_phase')} type={p.get('pipeline_type')}")

# Check how many total ideas, tasks, pipelines
ideas = fetch("/api/ideas/")
active_ideas = [i for i in ideas if i.get("status") not in ("done","cancelled","failed")]
print(f"\nSystem totals:")
print(f"  Ideas: {len(ideas)} total, {len(active_ideas)} active")
all_tasks = fetch("/api/tasks/")
done_tasks = [t for t in all_tasks if t.get("status") == "done"]
todo_count = [t for t in all_tasks if t.get("status") == "todo"]
ip_count = [t for t in all_tasks if t.get("status") == "in_progress"]
print(f"  Tasks: {len(all_tasks)} total, {len(done_tasks)} done, {len(todo_count)} todo, {len(ip_count)} in_progress")
print(f"  Pipelines: {len(pipelines)} total")
