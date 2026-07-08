"""Mark cycle30 idle idea as done."""
import json, urllib.request

# Fetch all ideas
resp = urllib.request.urlopen("http://127.0.0.1:8765/api/ideas/")
ideas = json.load(resp)

# Find cycle30 idle idea
target = None
for i in ideas:
    if "Idle cycle #30" in i["title"]:
        target = i["id"]
        break

if not target:
    print("Cycle30 idea not found")
    exit(1)

# Mark as done
data = json.dumps({"status": "done", "refined_description": "Auto health check cycle #30: all work completed."}).encode()
req = urllib.request.Request(
    f"http://127.0.0.1:8765/api/ideas/{target}",
    data=data,
    headers={"Content-Type": "application/json"},
    method="PATCH"
)
resp = urllib.request.urlopen(req)
result = json.load(resp)
print(f"Updated: {result['status']}")
