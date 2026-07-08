"""Check allowed methods on API endpoints."""
import json
import urllib.request

with urllib.request.urlopen("http://127.0.0.1:8765/openapi.json") as r:
    spec = json.load(r)

for path, methods in spec["paths"].items():
    if "ideas" in path:
        print(f"{path}: {list(methods.keys())}")
