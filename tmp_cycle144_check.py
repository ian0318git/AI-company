#!/usr/bin/env python3
"""Check pipeline status details."""
import json, sys, urllib.request

data = json.loads(urllib.request.urlopen('http://127.0.0.1:8765/api/pipelines/').read())
if data:
    print('Fields:', list(data[0].keys()))
print(f'Total: {len(data)}')
statuses = {}
for p in data:
    s = p.get('status', 'unknown')
    statuses[s] = statuses.get(s, 0) + 1
print('Status distrib:', statuses)
active = [p for p in data if p.get('status') not in ('done','completed','archived')]
print(f'Active pipelines: {len(active)}')
for p in active:
    print(f'  [{p.get("status")}] {p.get("id","")[:8]} | {p.get("pipeline_type", p.get("title","?"))[:50]}')
# Also show some completed ones just to see structure
if data:
    print("\nSample pipeline keys:")
    for k, v in data[0].items():
        print(f"  {k}: {str(v)[:60]}")
