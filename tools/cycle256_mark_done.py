#!/usr/bin/env python3
"""Mark repo cleanup as done after executing the work."""
import json, urllib.request

BASE = "http://127.0.0.1:8765/api"
idea_id = "917cb560-f175-4032-a8fc-9ff1c5d11a6f"

data = json.dumps({}).encode()
req = urllib.request.Request(BASE + "/ideas/" + idea_id + "/archive", data=data, method="PATCH")
req.add_header("Content-Type", "application/json")
try:
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read())
    print("Archive status:", result.get("status"))
except Exception as e:
    print("Archive error:", e)
    # Try marking as done via refine
    data2 = json.dumps({"status": "done"}).encode()
    req2 = urllib.request.Request(BASE + "/ideas/" + idea_id, data=data2, method="POST")
    req2.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req2) as r2:
            result2 = json.loads(r2.read())
        print("POST status:", result2.get("status"))
    except Exception as e2:
        print("POST error:", e2)
