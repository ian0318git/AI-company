import json, urllib.request

BASE = "http://127.0.0.1:8765"

def fetch(path):
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return json.loads(r.read())

projs = fetch("/api/projects/")
tasks = fetch("/api/tasks/")
pipes = fetch("/api/pipelines/")

targets = ["10c25577", "ae54db64"]
for p in projs:
    pid = p.get("id", "")
    for t in targets:
        if pid.startswith(t):
            print(f"Project: {p.get('name','?')[:60]} | id={pid[:20]}... | status={p.get('status','?')}")

print("\nTasks for Prompt Dashboard project:")
for t in tasks:
    if t.get("project_id","").startswith("ae54db64"):
        print(f"  [{t.get('status')}] {t.get('priority')} - {t.get('title')[:60]} (id={t.get('id','?')[:12]}...)")

print("\nPipelines for Prompt Dashboard project:")
for p in pipes:
    if p.get("project_id","").startswith("ae54db64"):
        print(f"  phase={p.get('current_phase')} type={p.get('pipeline_type')} (id={p.get('id','?')[:12]}...)")

print("\nEvolution Vaccine Injection project:")
for p in projs:
    if "Evolution Vaccine Injection into Task Execution" in p.get("name",""):
        ev_pid = p.get("id","")
        print(f"  id={ev_pid[:20]}... | status={p.get('status','?')}")
        for t in tasks:
            if t.get("project_id","") == ev_pid:
                print(f"  Task: [{t.get('status')}] {t.get('title')[:60]}")
        for pl in pipes:
            if pl.get("project_id","") == ev_pid:
                print(f"  Pipeline: phase={pl.get('current_phase')} type={pl.get('pipeline_type')}")

print("\nAutonomous Idea Generator project:")
for p in projs:
    if "Autonomous Idea Generator" in p.get("name","") and "Self-Seeding" in p.get("name",""):
        pid = p.get("id","")
        print(f"  id={pid[:20]}... | status={p.get('status','?')}")
        for t in tasks:
            if t.get("project_id","") == pid:
                print(f"  Task: [{t.get('status')}] {t.get('title')[:60]}")
        for pl in pipes:
            if pl.get("project_id","") == pid:
                print(f"  Pipeline: phase={pl.get('current_phase')} type={pl.get('pipeline_type')}")
