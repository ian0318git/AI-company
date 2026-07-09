#!/usr/bin/env python3
"""Cycle 58 — system state inspection"""
import json, urllib.request, sys
from collections import Counter

API = "http://127.0.0.1:8765/api"

def get(endpoint):
    with urllib.request.urlopen(f"{API}/{endpoint}") as r:
        return json.loads(r.read())

# Pipelines
pipelines = get("pipelines/")
print(f"=== PIPELINES ({len(pipelines)}) ===")
c1 = Counter(p.get("status","?") for p in pipelines)
c2 = Counter(p.get("current_phase","?") for p in pipelines)
print("status:", dict(c1))
print("current_phase:", dict(c2))

# Show pipelines that are NOT in a terminal phase
terminal_phases = {"done", "completed", "failed", "cancelled"}
in_flight = [p for p in pipelines if p.get("current_phase","") not in terminal_phases]
print(f"\nIn-flight pipelines (phase != done/completed/failed): {len(in_flight)}")
for p in in_flight:
    print(f"  {p['id'][:8]} type={p.get('pipeline_type')} phase={p.get('current_phase')} status={p.get('status')}")

# Tasks
tasks = get("tasks/")
print(f"\n=== TASKS ({len(tasks)}) ===")
c3 = Counter(t.get("status","?") for t in tasks)
print("statuses:", dict(c3))

# Ideas
ideas = get("ideas/")
print(f"\n=== IDEAS ({len(ideas)}) ===")
c4 = Counter(i.get("status","?") for i in ideas)
print("statuses:", dict(c4))
# Show non-done non-archived
active_ideas = [i for i in ideas if i.get("status") not in ("done","archived")]
print(f"Active (not done/archived): {len(active_ideas)}")
for i in active_ideas:
    print(f"  [{i['status']}] {i['title']}")
# Also show newest
newest = sorted(ideas, key=lambda x: x.get("created_at",""), reverse=True)[:3]
print("\n3 newest ideas:")
for i in newest:
    print(f"  [{i['status']}] {i['title']}")
