"""Check the latest idea."""
import json
import urllib.request

with urllib.request.urlopen("http://127.0.0.1:8765/api/ideas/") as r:
    data = json.load(r)

latest = data[-1]
print(json.dumps(latest, indent=2, default=str))
