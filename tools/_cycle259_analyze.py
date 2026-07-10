#!/usr/bin/env python3
"""Analyze tasks and projects for cycle 259."""
import json, sys, os
from collections import Counter

def fetch(path):
    import urllib.request
    url = f"http://127.0.0.1:8765{path}"
    with urllib.request.urlopen(url) as r:
        return json.loads(r.read())

tasks = fetch("/api/tasks/?limit=300")
projects = fetch("/api/projects/?limit=300")

print("="*60)
print("TASKS")
print("="*60)
statuses = Counter(i["status"] for i in tasks["items"])
print("Status counts:", dict(statuses))

pending = [i for i in tasks["items"] if i["status"] in ("pending", "open", "todo")]
print(f"\nPending tasks ({len(pending)}):")
for t in sorted(pending, key=lambda x: {"high":0,"medium":1,"low":2}.get(x.get("priority","medium"), 1)):
    pid = t.get("project_id","?")[:8]
    print(f'  [{t.get("priority","?"):>6}] {t["id"][:8]} | {t["title"][:80]} | proj={pid}')

inp = [i for i in tasks["items"] if i["status"] == "in_progress"]
print(f"\nIn progress ({len(inp)}):")
for t in inp:
    print(f'  [{t.get("priority","?"):>6}] {t["id"][:8]} | {t["title"][:80]}')

print("\n" + "="*60)
print("PROJECTS")
print("="*60)
pstatuses = Counter(i["status"] for i in projects["items"])
print("Status counts:", dict(pstatuses))

for p in projects["items"]:
    print(f'  [{p.get("status","?"):>10}] {p.get("id","?")[:8]} | {p.get("title","?")[:70]} | phase={p.get("pipeline_phase","?")}')
