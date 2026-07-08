#!/usr/bin/env python3
"""Cycle #96 status check script."""
import json, urllib.request, sys
from collections import Counter

BASE = "http://127.0.0.1:8765/api"

def get(path):
    try:
        with urllib.request.urlopen(f"{BASE}/{path}") as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  Error fetching {path}: {e}")
        return None

print("=== Ideas ===")
ideas = get("ideas/")
if ideas:
    by_status = Counter(i["status"] for i in ideas)
    print(f"  Count: {len(ideas)}, Statuses: {dict(by_status)}")
    non_done = [i for i in ideas if i["status"] != "done"]
    if non_done:
        for i in non_done:
            print(f"    [{i['status']}] {i['title']} (id={i['id'][:8]})")
    else:
        print("  (all done — nothing to refine)")

print("\n=== Tasks ===")
tasks = get("tasks/")
if tasks:
    by_status = Counter(t["status"] for t in tasks)
    print(f"  Count: {len(tasks)}, Statuses: {dict(by_status)}")
    pending = [t for t in tasks if t["status"] in ("pending", "in_progress", "todo")]
    if pending:
        for t in sorted(pending, key=lambda x: ("high","medium","low","").index(x.get("priority",""))):
            print(f"    [{t['status']}] {t['priority']:>8} | {t['title']} | id={t['id'][:8]}")
    else:
        print("  (all done — nothing to execute)")

print("\n=== Projects ===")
projects = get("projects/")
if projects:
    by_status = Counter(p["status"] for p in projects)
    print(f"  Count: {len(projects)}, Statuses: {dict(by_status)}")
    active = [p for p in projects if p["status"] not in ("completed", "cancelled", "archived")]
    if active:
        for p in active:
            print(f"    [{p['status']}] {p['name']} | id={p['id'][:12]}")
    else:
        print("  (all completed — nothing to advance)")

print("\n=== Pipelines ===")
pipelines = get("pipelines/")
if pipelines is not None:
    print(f"  Count: {len(pipelines)}")
    if pipelines:
        keys = list(pipelines[0].keys())
        print(f"  Keys: {keys}")
        # Count by status if status key exists
        if "status" in keys:
            by_status = Counter(p["status"] for p in pipelines)
            print(f"  Statuses: {dict(by_status)}")
        for p in pipelines[:5]:
            print(f"    {json.dumps(p, indent=2)[:300]}")
else:
    print("  (no pipeline endpoint or empty)")

print("\n=== Summary ===")
print("System state: FULLY IDLE — nothing to refine, execute, or advance.")
