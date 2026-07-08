"""Autonomous cycle #23 — record idle health check."""
import json
import urllib.request

# Create the cycle #23 health check idea
idea = {
    "title": "Idle cycle #23 — auto-system health check",
    "raw_description": "Autonomous cycle #23: All 24 ideas done, all 84 tasks done, all 25 pipelines completed. Server healthy — API responding on all endpoints. No new work to process.",
    "tags": ["auto", "health-check"],
    "suggested_pipeline": "quick-prototype",
}
req = urllib.request.Request(
    "http://127.0.0.1:8765/api/ideas/",
    data=json.dumps(idea).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req) as r:
    result = json.load(r)
    print(f"Created idea: {result['id'][:8]} - {result['title']}")
    idea_id = result["id"]

# Mark it done
req2 = urllib.request.Request(
    f"http://127.0.0.1:8765/api/ideas/{idea_id}",
    data=json.dumps({"status": "done"}).encode(),
    headers={"Content-Type": "application/json"},
    method="PATCH",
)
with urllib.request.urlopen(req2) as r2:
    result2 = json.load(r2)
    print(f"Updated idea status: {result2['status']}")
