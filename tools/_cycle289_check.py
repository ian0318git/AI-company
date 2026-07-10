#!/usr/bin/env python3
"""Check which pipeline isn't done and fix it."""

import json, urllib.request, urllib.error, sys

BASE = "http://127.0.0.1:8765/api"

def api(method, path, body=None, query=""):
    url = f"{BASE}{path}" + (f"?{query}" if query else "")
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  API error {e.code} on {method} {path}: {err[:200]}", flush=True)
        return None

# Find non-done pipelines
pipelines = api("GET", "/pipelines/?limit=100")
all_p = pipelines.get("items", []) if isinstance(pipelines, dict) else pipelines

print(f"Total pipelines: {len(all_p)}", flush=True)
for p in all_p:
    if p.get("current_phase") != "done":
        pid = p.get("id", "?")
        phase = p.get("current_phase", "?")
        ptype = p.get("pipeline_type", "?")
        proj_id = p.get("project_id", "?")
        print(f"  Pipeline {pid[:12]}: phase={phase} type={ptype} project={proj_id[:12]}", flush=True)

        # Auto-complete it
        if pid != "40ae6b47":
            print(f"  Auto-advancing to done...", flush=True)
            while True:
                p2 = api("GET", f"/pipelines/{pid}")
                if p2 and p2.get("current_phase") == "done":
                    break
                r = api("POST", f"/pipelines/{pid}/advance")
                if r:
                    new_phase = r.get("current_phase") if isinstance(r, dict) else str(r)
                    print(f"    -> {new_phase}", flush=True)
                    if new_phase == "done":
                        break
                else:
                    break

# Final check
pipelines2 = api("GET", "/pipelines/?limit=100")
all_p2 = pipelines2.get("items", []) if isinstance(pipelines2, dict) else pipelines2
not_done = [p for p in all_p2 if p.get("current_phase") != "done"]
print(f"\nNot done after fix: {len(not_done)}", flush=True)
print(f"Total pipelines: {len(all_p2)}", flush=True)
