#!/usr/bin/env python3
import json, subprocess, sys

raw = subprocess.check_output(["curl", "-s", "http://127.0.0.1:8765/api/pipelines/"])
data = json.loads(raw)

print("=== Active Pipelines ===")
active = [p for p in data if p.get("current_phase") != "done"]
for p in active:
    print(f"  {p['pipeline_type']:20s} | {p['current_phase']:20s} | project={p['project_id'][:8]}")

print()
print("=== Just Completed (via advance) ===")
completed = [p for p in data if p.get("current_phase") == "done"]
print(f"  Total completed pipelines: {len(completed)}")
for p in completed:
    print(f"  - {p['pipeline_type']:20s} id={p['id'][:8]}")
