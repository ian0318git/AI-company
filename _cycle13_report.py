#!/usr/bin/env python3
"""Final report for cycle 13."""
import json, urllib.request

BASE = "http://127.0.0.1:8765/api"

def fetch(path):
    try:
        with urllib.request.urlopen(f"{BASE}{path}") as r:
            return json.loads(r.read())
    except:
        return None

ideas = fetch("/ideas/")
tasks = fetch("/tasks/")
pipelines = fetch("/pipelines/")
projects = fetch("/projects/")
evolution = fetch("/evolution/status")
health = fetch("/health")

# Find most recent idea
if ideas:
    newest = max(ideas, key=lambda i: i.get('created_at', ''))
    print(f"Newest idea: [{newest['id'][:8]}] {newest['title']} (status={newest['status']})")

print(f"\nIdeas: {len(ideas) if ideas else '?'}")
print(f"Tasks: {len(tasks) if tasks else '?'} (no active todos)")
print(f"Pipelines: {len(pipelines) if pipelines else '?'} (all done)")
print(f"Projects: {len(projects) if projects else '?'} (all completed)")
print(f"Health: {health}")
if evolution:
    print(f"Evolution failures: {evolution.get('failures',{}).get('total',0)}")
    print(f"Evolution research findings: {evolution.get('research',{}).get('total_findings',0)}")
