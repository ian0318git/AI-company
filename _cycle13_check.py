#!/usr/bin/env python3
"""Check cycle 13 state: tasks, pipelines, ideas."""
import json, urllib.request

BASE = "http://127.0.0.1:8765/api"

def fetch(path):
    try:
        with urllib.request.urlopen(f"{BASE}{path}") as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  ERR {path}: {e}")
        return None

# Ideas: find non-done
ideas = fetch("/ideas/")
if ideas:
    active_ideas = [i for i in ideas if i.get("status") not in ("done", "completed")]
    print(f"Ideas: {len(ideas)} total, {len(active_ideas)} active")
    for i in active_ideas[:10]:
        print(f"  [{i['id'][:8]}] {i['title']} (status={i['status']})")

# Tasks: find pending/in_progress, sorted by priority
tasks = fetch("/tasks/")
if tasks:
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    active = [t for t in tasks if t.get('status') in ('pending', 'in_progress')]
    active.sort(key=lambda t: (priority_order.get(t.get('priority','low'), 99), t.get('created_at','')))
    print(f"\nTasks: {len(tasks)} total, {len(active)} active")
    for t in active[:20]:
        print(f"  [{t.get('priority','?')}] {t['title']} (status={t['status']})")

# Pipelines: find non-done
pipelines = fetch("/pipelines/")
if pipelines:
    active_p = [p for p in pipelines if p.get('phase') not in ('done', 'completed')]
    print(f"\nPipelines: {len(pipelines)} total, {len(active_p)} active")
    for p in active_p[:10]:
        print(f"  [{p['id'][:8]}] phase={p.get('phase','?')} idea={p.get('idea_id','')[:8]}")

# Projects: find non-done
projects = fetch("/projects/")
if projects:
    active_pr = [pr for pr in projects if pr.get('status') not in ('done', 'completed')]
    print(f"\nProjects: {len(projects)} total, {len(active_pr)} active")
    for pr in active_pr[:10]:
        print(f"  [{pr['id'][:8]}] {pr.get('name','?')} (status={pr.get('status','?')})")
