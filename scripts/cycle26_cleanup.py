"""Cancel stale tasks from completed idle projects for cycle 26."""
import json, urllib.request

# Cycle #25 stale task IDs
stale_ids = [
    "2880b4ae-c6be-47c4-a4f0-590c190934ba",
    "7a2bdb64-462d-4f24-8970-fafee1b1c885",
    "d41ca879-1c5b-4d79-bfa2-b90920bc7260",
    "dad132de-50b1-44b4-881a-ae3ca00e3823",
    "8f8854a9-ab1c-4d01-b576-6e1bfbc40a12",
    "0555a412-2409-4c0e-9591-25f7cb12635d",
    "14edb188-1521-444d-b939-e54be3cb36ff",
]

count = 0
for tid in stale_ids:
    req = urllib.request.Request(
        f"http://127.0.0.1:8765/api/tasks/{tid}/status?status=cancelled",
        method="PATCH",
    )
    resp = urllib.request.urlopen(req)
    body = json.loads(resp.read())
    if body.get("status") == "cancelled":
        count += 1
        print(f"  Cancelled: {tid[:8]}...")
    else:
        print(f"  Failed: {tid[:8]}... -> {body.get('status')}")

print(f"\nCancelled {count}/{len(stale_ids)} stale tasks")
