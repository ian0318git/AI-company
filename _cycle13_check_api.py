#!/usr/bin/env python3
"""Check task and pipeline API endpoints."""
import json, urllib.request

BASE = "http://127.0.0.1:8765"

with urllib.request.urlopen(f"{BASE}/openapi.json") as r:
    spec = json.loads(r.read())

paths = spec.get('paths', {})
for path, methods in sorted(paths.items()):
    if 'task' in path:
        print(f"{path}:")
        for method, details in methods.items():
            print(f"  {method}: {details.get('summary','')}")
            if 'requestBody' in details:
                content = details['requestBody'].get('content', {})
                for ct, schema_info in content.items():
                    print(f"    body ({ct}): schema keys = {list(schema_info.get('schema',{}).keys())}")
