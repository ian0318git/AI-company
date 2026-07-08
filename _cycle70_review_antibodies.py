"""Cycle #70: Review and approve pending antibody candidates."""
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8765"

# Fetch candidates
resp = urllib.request.urlopen(f"{BASE}/api/evolution/antibody-candidates")
candidates = json.loads(resp.read())

print(f"Found {len(candidates)} candidates pending review")

approved_count = 0
for c in candidates:
    cid = c["id"]
    title = c["title"][:60]
    payload = json.dumps({
        "action": "approve"
    }).encode()
    req = urllib.request.Request(
        f"{BASE}/api/evolution/antibody-candidates/{cid}/review",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp2 = urllib.request.urlopen(req)
        result = json.loads(resp2.read())
        print(f"  [OK] {title}")
        print(f"       Status: {result.get('status', 'unknown')}")
        approved_count += 1
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  [ERR] {title} -> HTTP {e.code}: {body[:120]}")

# Check final evolution status
resp3 = urllib.request.urlopen(f"{BASE}/api/evolution/status")
status = json.loads(resp3.read())
print(f"\nEvolution status after approval:")
print(f"  Antibodies active: {status['failures']['antibodies_active']}")
print(f"  Vaccines active:   {status['failures']['vaccines_active']}")
print(f"  Health:            {status['evolution_health']}")
