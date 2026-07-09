#!/usr/bin/env python3
"""Check pipeline current_phase values."""
import json, urllib.request
from collections import Counter

data = json.loads(urllib.request.urlopen('http://127.0.0.1:8765/api/pipelines/').read())
c = Counter(p.get('current_phase') for p in data)
print('Phase distribution:', dict(c))
active = [p for p in data if p.get('current_phase') != 'done']
print(f'\nNot-done pipelines: {len(active)}')
for p in active:
    print(f'  phase={p["current_phase"]:>12} | {p["id"][:8]} | {p["pipeline_type"][:20]}')
print('\nDone.')
