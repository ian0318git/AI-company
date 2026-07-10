#!/usr/bin/env python3
"""Check state and fix pipeline-type matching directly."""
import json, urllib.request, urllib.error, sys, os, time

BASE = "http://127.0.0.1:8765/api"

def api(method, path, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        return {"_error": f"{e.code}: {err[:200]}"}
    except Exception as e:
        return {"_error": str(e)}

# Check current state
print("=== Ideas ===")
ideas = api("GET", "/ideas/")
for i in ideas.get("items", []):
    if i["status"] in ("in_progress", "refining", "new"):
        print(f"  [{i['status']}] {i['title'][:60]}")
        print(f"    suggested_pipeline: {i.get('suggested_pipeline')}")
        print(f"    tags: {i.get('tags')}")

# Check stuck pipeline
print("\n=== Pipelines ===")
pipes = api("GET", "/pipelines/")
stuck = [p for p in pipes if p["current_phase"] != "done"]
print(f"Stuck: {len(stuck)}")
for p in stuck:
    print(f"  {p['id'][:12]} phase={p['current_phase']} type={p['pipeline_type']}")

if stuck:
    # Advance it
    pid = stuck[0]["id"]
    for _ in range(8):
        r = api("POST", f"/pipelines/{pid}/advance", {})
        if r and r.get("_error"):
            print(f"  Error advancing: {r['_error']}")
            break
        cp = r.get("current_phase") or (r.get("pipeline") or {}).get("current_phase", "?") if r else "?"
        print(f"  -> {cp}")
        if cp == "done":
            break
        time.sleep(0.2)

# Now fix the pipeline-type matching bug in the source code
print("\n=== Fixing pipeline-type matching ===")
target = os.path.expanduser("/home/ian/github-project/AI-company/src/ai_embedded_company/api/routes/ideas.py")
with open(target) as f:
    content = f.read()

# Bug: quick-prototype scores 1 base, but get's easily beaten if ANY keyword matches another pipeline type
# Fix: boost quick-prototype when ALL negative keywords exclude other types
# Also: ensure the suggested_pipeline from the idea creation is respected as a tiebreaker

# Specific fix: the backend-only fallback doesn't check tags, only desc_lower
# And the suggested_pipeline from POST isn't given priority in _refine_idea

# Add suggested_pipeline hint to the scoring, after the backend-only check
old = """    best = max(scores, key=scores.get)
    best_score = scores[best]
    suggested_pipeline = best if best_score > 0 else "quick-prototype"""

new = """    # HINT: if the caller explicitly passed a suggested_pipeline, boost it by 1
    if payload and payload.suggested_pipeline:
        hint = payload.suggested_pipeline
        if hint in scores:
            scores[hint] += 1

    best = max(scores, key=scores.get)
    best_score = scores[best]
    suggested_pipeline = best if best_score > 0 else "quick-prototype"""

if old in content:
    content = content.replace(old, new)
    with open(target, "w") as f:
        f.write(content)
    print("  Fixed: _refine_idea now respects hint from suggested_pipeline payload")
else:
    print("  Pattern not found (may already be patched)")

# Also fix the embedded_negative to include "auto-seed" (auto-seeded maintenance ideas shouldn't get embedded)
old2 = "embedded_negative = [\"web\", \"frontend\", \"react\", \"vue\", \"api\", \"backend\",\n                         \"\\u7d14\\u8edf\\u9ad4\", \"software-only\", \"maintenance\"]"
new2 = "embedded_negative = [\"web\", \"frontend\", \"react\", \"vue\", \"api\", \"backend\",\n                         \"\\u7d14\\u8edf\\u9ad4\", \"software-only\", \"maintenance\", \"auto-seed\"]"

if old2 in content:
    content = content.replace(old2, new2)
    with open(target, "w") as f:
        f.write(content)
    print("  Fixed: added 'auto-seed' to embedded_negative keywords")
else:
    print("  embedded_negative pattern not found")

print("\n=== Done ===")
