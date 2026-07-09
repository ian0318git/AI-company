#!/usr/bin/env python3
"""Check current state for cycle #62."""
import json, urllib.request

BASE = "http://127.0.0.1:8765/api"

# Tasks
try:
    tasks = json.loads(urllib.request.urlopen(f"{BASE}/tasks/").read())
    todo = [t for t in tasks if t.get("status") not in ("done", "cancelled", "archived")]
    print("=== TODO TASKS ===")
    for t in todo:
        print(f"  ID:{t['id'][:8]} | {t['title']} | stat:{t['status']} | pri:{t.get('priority','?')}")
    print(f"  Pending: {len(todo)}/{len(tasks)}")
except Exception as e:
    print(f"Tasks error: {e}")

# Pipelines
try:
    pipes = json.loads(urllib.request.urlopen(f"{BASE}/pipelines/").read())
    items = pipes if isinstance(pipes, list) else [pipes]
    print("\n=== PIPELINES ===")
    for p in items:
        print(f"  ID:{p.get('id','?')[:12]} | Idea:{p.get('idea_title','?')} | Status:{p.get('status','?')} | Phase:{p.get('current_phase','?')}")
    print(f"  Total: {len(items)}")
except Exception as e:
    print(f"Pipelines error: {e}")

# Ideas - check for non-done, non-archived
try:
    ideas = json.loads(urllib.request.urlopen(f"{BASE}/ideas/").read())
    active = [i for i in ideas if i.get("status") not in ("done", "cancelled", "archived")]
    print("\n=== ACTIVE IDEAS ===")
    for i in active:
        refined = "yes" if i.get("refined_description") else "no"
        print(f"  ID:{i['id'][:8]} | {i['title']} | status:{i['status']} | refined:{refined} | pipeline:{i.get('suggested_pipeline','?')}")
    print(f"  Active: {len(active)}/{len(ideas)}")

    # New ideas (no refined desc) that aren't archived/done
    new_ideas = [i for i in ideas if i.get("status") not in ("done", "cancelled", "archived") and not i.get("refined_description")]
    print(f"\n=== NEW IDEAS (unrefined) ===")
    for i in new_ideas:
        print(f"  ID:{i['id'][:8]} | {i['title']} | tags:{i.get('tags',[])}")
    if not new_ideas:
        print("  None found.")
except Exception as e:
    print(f"Ideas error: {e}")

# High-priority tasks
try:
    tasks = json.loads(urllib.request.urlopen(f"{BASE}/tasks/").read())
    high_prio = [t for t in tasks if t.get("status") not in ("done", "cancelled", "archived") and t.get("priority") in ("high", "critical")]
    print(f"\n=== HIGH-PRIORITY TODO ===")
    for t in high_prio:
        print(f"  ID:{t['id'][:8]} | {t['title']} | pri:{t['priority']}")
    if not high_prio:
        print("  None found.")
except Exception as e:
    print(f"High-pri error: {e}")
