"""Check the newest idea by created_at."""
import json
import urllib.request

with urllib.request.urlopen("http://127.0.0.1:8765/api/ideas/") as r:
    data = json.load(r)

# Sort by created_at descending
data.sort(key=lambda x: x["created_at"], reverse=True)
for idea in data[:3]:
    print(json.dumps(idea, indent=2, default=str))
    print("---")
