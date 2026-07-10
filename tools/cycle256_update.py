#!/usr/bin/env python3
"""Quick test to update idea status."""
import json, urllib.request

BASE = "http://127.0.0.1:8765/api"
idea_id = "da9bf5b6-e6af-4704-8987-53b35ac74981"

# Try PUT
data = json.dumps({"status": "done"}).encode()
req = urllib.request.Request(BASE + "/ideas/" + idea_id, data=data, method="PUT")
req.add_header("Content-Type", "application/json")
try:
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read())
    print("PUT status:", result.get("status"))
except urllib.error.HTTPError as e:
    body = e.read().decode()[:300]
    print("PUT error:", e.code, body)
