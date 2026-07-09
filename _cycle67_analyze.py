#!/usr/bin/env python3
import json, sys
data = json.load(sys.stdin)
phases = {}
types = {}
for p in data:
    ph = p.get("current_phase", "unknown")
    phases[ph] = phases.get(ph, 0) + 1
    t = p.get("pipeline_type", "unknown")
    types[t] = types.get(t, 0) + 1
print(f"Pipelines by phase: {phases}")
print(f"Pipelines by type: {types}")
print(f"Total pipelines: {len(data)}")
