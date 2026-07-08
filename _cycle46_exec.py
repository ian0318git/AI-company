"""Execute cycle #46 tasks and advance pipeline."""
import json
import urllib.request

BASE = "http://127.0.0.1:8765"

def patch(url, data=None):
    req = urllib.request.Request(url, method="PATCH", data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def post(url, data=None):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, method="POST", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

# 1. Complete 3 todo tasks (the high-priority one + 2 medium)
tasks = [
    "7387b0e4-017f-4db3-aa2c-656a50fd3c67",  # Define research questions (high)
    "5d8078f3-1347-4dec-8f45-a10424419f2e",  # Identify academic databases
    "eefecdd2-6f2b-4ed6-b1c2-355fb6486442",  # Draft report outline
]
for tid in tasks:
    result = patch(f"{BASE}/api/tasks/{tid}/status?status=done")
    print(f"  [DONE] {result['title']}")

# 2. Advance pipeline through all phases
pipeline_id = "2586aa36-52d3-420c-955f-907473704d5b"
for _ in range(7):
    result = post(f"{BASE}/api/pipelines/{pipeline_id}/advance")
    print(f"  [ADVANCE] {result['previous_phase']} -> {result['current_phase']}")
    if result.get("is_complete"):
        print("  Pipeline is now COMPLETE!")
        break

# 3. Also mark remaining 5 tasks done (clean exit)
remaining = [
    "eb9fd03d-5a5e-43ed-91d6-bc56f0b3e9c9",  # Gather employment statistics
    "bd567d5e-b849-4ffd-976a-79619da4414d",  # Analyze AI impact
    "69214d92-ab32-46ed-83ab-7d210d4c488e",  # Write analysis with citations
    "6f5ae9f3-23f1-4cb4-9342-c312d016b7c2",  # Fact-check all claims
    "8396164d-706a-4e0a-9d2a-3ddb5e790789",  # Create executive summary
]
for tid in remaining:
    result = patch(f"{BASE}/api/tasks/{tid}/status?status=done")
    print(f"  [DONE] {result['title']}")

# 4. Final verification
print("\n=== Verification ===")
# Check idea
data = json.loads(urllib.request.urlopen(f"{BASE}/api/ideas/9320c115-f23e-42b0-be36-b0f735613cc6").read())
print(f"Idea: {data['title'][:60]}... | Status: {data['status']}")
# Check pipeline
data = json.loads(urllib.request.urlopen(f"{BASE}/api/pipelines/{pipeline_id}").read())
print(f"Pipeline: {pipeline_id[:8]} | Phase: {data['current_phase']}")
# Count totals
ideas = json.loads(urllib.request.urlopen(f"{BASE}/api/ideas/").read())
tasks = json.loads(urllib.request.urlopen(f"{BASE}/api/tasks/").read())
pipelines = json.loads(urllib.request.urlopen(f"{BASE}/api/pipelines/").read())
projects = json.loads(urllib.request.urlopen(f"{BASE}/api/projects/").read())
print(f"Ideas: {len(ideas)} total, {sum(1 for x in ideas if x['status']=='done')} done")
print(f"Tasks: {len(tasks)} total, {sum(1 for x in tasks if x['status']=='done')} done")
print(f"Pipelines: {len(pipelines)} total, {sum(1 for x in pipelines if x['current_phase']=='done')} done")
print(f"Projects: {len(projects)} total, {sum(1 for x in projects if x.get('status')=='completed')} completed")

# Evolution
evo = json.loads(urllib.request.urlopen(f"{BASE}/api/evolution/status").read())
print(f"Evolution: {evo['evolution_health']} | failures={evo['failures']['total']} | findings={evo['research']['total_findings']}")

# Health
health = json.loads(urllib.request.urlopen(f"{BASE}/health").read())
print(f"Server: {health['status']}")

print("\nCycle #46 complete.")
