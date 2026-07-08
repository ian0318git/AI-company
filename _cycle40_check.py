"""Cycle 40 — check system state: ideas, tasks, pipelines, projects."""
import json, subprocess, sys
from urllib.request import urlopen

BASE = "http://127.0.0.1:8765"

def fetch(path):
    try:
        return json.loads(urlopen(f"{BASE}{path}").read())
    except Exception as e:
        print(f"Error fetching {path}: {e}")
        return None

print("=== HEALTH ===")
health = fetch("/api/health/")
if health:
    print(json.dumps(health, indent=2)[:400])
else:
    print("No health endpoint or error")

print("\n=== IDEAS ===")
ideas = fetch("/api/ideas/")
if ideas:
    raw = [i for i in ideas if i.get("status") == "raw"]
    refined = [i for i in ideas if i.get("status") == "refined"]
    ip = [i for i in ideas if i.get("status") == "in_progress"]
    done = [i for i in ideas if i.get("status") == "done"]
    print(f"Total: {len(ideas)} | raw={len(raw)} refined={len(refined)} in_progress={len(ip)} done={len(done)}")
    if raw: [print(f"  RAW: {i['id'][:12]} {i['title'][:60]}") for i in raw]
    if refined: [print(f"  REFINED: {i['id'][:12]} {i['title'][:60]}") for i in refined]
    if ip: [print(f"  IN_PROGRESS: {i['id'][:12]} {i['title'][:60]}") for i in ip]

print("\n=== TASKS ===")
tasks = fetch("/api/tasks/")
if tasks:
    pending = [t for t in tasks if t.get("status") != "done"]
    print(f"Total: {len(tasks)} | pending: {len(pending)}")
    if pending:
        for t in pending:
            print(f"  {t['status']:10} pri={t.get('priority','?'):6} {t['id'][:12]} {t['title'][:60]}")

print("\n=== PIPELINES ===")
pipes = fetch("/api/pipelines/")
if pipes:
    # Use current_phase field
    active = [p for p in pipes if p.get("current_phase") not in ("completed","done")]
    print(f"Total: {len(pipes)} | active: {len(active)} | all_done: {all(p.get('current_phase')=='done' for p in pipes)}")
    if active:
        for p in active:
            print(f"  phase={p.get('current_phase')} type={p.get('pipeline_type')} project={str(p.get('project_id','?'))[:12]}")
    # Show latest
    for p in sorted(pipes, key=lambda x: x.get("created_at",""), reverse=True)[:3]:
        print(f"  latest: {p.get('id','?')[:12]} phase={p.get('current_phase')} type={p.get('pipeline_type')} created={p.get('created_at','')[:19]}")

print("\n=== PROJECTS ===")
projects = fetch("/api/projects/")
if projects:
    active = [p for p in projects if p.get("status") not in ("completed","done")]
    print(f"Total: {len(projects)} | active: {len(active)}")
    if active:
        for p in active:
            print(f"  {p.get('id','?')[:12]} {p.get('name','?')} {p.get('status')}")

print("\n=== SUMMARY ===")
all_idle = (
    (ideas is not None and all(i.get("status") in ("done",) for i in ideas)) and
    (tasks is not None and all(t.get("status") == "done" for t in tasks)) and
    (pipes is not None and all(p.get("current_phase") == "done" for p in pipes)) and
    (projects is not None and all(p.get("status") in ("completed","done") for p in projects))
)
print(f"System idle: {all_idle}")
if all_idle:
    print(f"Ideas all done, tasks all done, pipelines all phase=done, projects all completed.")
    print("No new work to process. System healthy.")
