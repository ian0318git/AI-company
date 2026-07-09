#!/usr/bin/env python3
"""Fetch OpenAPI spec and find task/pipeline-related endpoints."""
import json, subprocess, sys
r = subprocess.run(['curl', '-s', 'http://127.0.0.1:8765/openapi.json'], capture_output=True, text=True)
spec = json.loads(r.stdout)
# Find paths related to tasks and pipelines
for path, methods in sorted(spec.get('paths', {}).items()):
    if any(kw in path for kw in ['task', 'pipeline', 'idea', 'project']):
        for method, details in methods.items():
            summary = details.get('summary', '')
            print("%s %s  # %s" % (method.upper(), path, summary))
