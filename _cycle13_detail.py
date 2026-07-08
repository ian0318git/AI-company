#!/usr/bin/env python3
"""Detailed check of pipelines."""
import json, urllib.request

BASE = "http://127.0.0.1:8765/api"

def fetch(path):
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return json.loads(r.read())

p = fetch("/pipelines/")
print(f"Total pipelines: {len(p)}")
if p:
    # Show keys
    all_keys = set()
    for pl in p:
        all_keys.update(pl.keys())
    print(f"All keys: {all_keys}")

    # Phase distribution
    from collections import Counter
    phases = Counter(pl.get('phase', 'MISSING') for pl in p)
    print(f"Phase distribution: {dict(phases)}")
    statuses = Counter(pl.get('status', 'MISSING') for pl in p)
    print(f"Status distribution: {dict(statuses)}")

    # Show full record of first one
    if p:
        print("\nFirst pipeline record:")
        print(json.dumps(p[0], indent=2, default=str))
