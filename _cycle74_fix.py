"""Fix cycle 74 - investigate Evolution Vaccine pipeline and task status."""
import json, urllib.request, urllib.error

BASE = "http://127.0.0.1:8765"

def fetch(method, path, data=None):
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "detail": e.read().decode()[:500]}

# Investigate Evolution Vaccine pipeline
print("=== Evolution Vaccine Injection into Task Execution ===")
# Look for the idea
ideas = fetch("GET", "/api/ideas/")
ev_idea = [i for i in ideas if i.get("id","").startswith("eff87aaf")]
if ev_idea:
    i = ev_idea[0]
    print(f"Idea: {i['title'][:60]}")
    print(f"  status={i['status']} project_id={i.get('project_id','?')[:20]}...")

# Look for the project
projects = fetch("GET", "/api/projects/")
ev_project = [p for p in projects if "Evolution Vaccine Injection into Task Execution" in p.get("name","")]
if ev_project:
    p = ev_project[0]
    print(f"Project: {p['name'][:60]}")
    print(f"  id={p['id'][:20]}... status={p.get('status','?')}")
    # Look for pipeline by project_id
    pipelines = fetch("GET", f"/api/pipelines/?project_id={p['id']}")
    for pl in pipelines:
        print(f"  Pipeline: id={pl['id'][:20]}... phase={pl.get('current_phase','?')} type={pl.get('pipeline_type','?')} idea_id={pl.get('idea_id','?')[:20]}...")
else:
    # Search all projects more broadly
    for p in projects:
        name = p.get("name","")
        if "Evolution" in name and "Vaccine" in name:
            print(f"Project: {name[:60]} id={p['id'][:20]}... status={p.get('status','?')}")

# Try to find pipeline directly
pipelines_all = fetch("GET", "/api/pipelines/")
for pl in pipelines_all:
    if pl.get("idea_id","") and "eff87aaf" in pl.get("idea_id",""):
        print(f"Direct pipeline match: id={pl['id'][:20]}... phase={pl.get('current_phase','?')} idea_id={pl.get('idea_id','?')[:20]}...")

# Check if that specific idea already has a different project
for i in ideas:
    if i.get("title","") and "Evolution Vaccine Injection into Task Execution" in i.get("title",""):
        print(f"Found idea by title: id={i['id'][:20]}... status={i.get('status','?')} project_id={i.get('project_id','?')[:20]}...")

# Check task status update response format
print("\n=== Task status update response ===")
tasks = fetch("GET", "/api/tasks/")
todo_tasks = [t for t in tasks if t.get("project_id","").startswith("ae54db64") and t.get("status") == "in_progress"]
for t in todo_tasks[:3]:
    print(f"  Task: {t['title'][:50]} status={t.get('status','?')}")
