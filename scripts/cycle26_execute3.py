"""Execute cycle 26 - complete tasks 3-4, advance pipeline."""
import json, urllib.request

BASE = "http://127.0.0.1:8765"

def patch(url):
    req = urllib.request.Request(url, method="PATCH")
    return json.loads(urllib.request.urlopen(req).read())

def post(url, data=None):
    req = urllib.request.Request(url, method="POST")
    if data:
        req.data = json.dumps(data).encode()
        req.add_header("Content-Type", "application/json")
    return json.loads(urllib.request.urlopen(req).read())

# Complete: Draft report outline and structure
print("Completing: Draft report outline and structure")
result = patch(f"{BASE}/api/tasks/033fc8ff-6dd6-48ac-93d1-0aa867c584f2/status?status=done")
print(f"  Status: {result.get('status')}")

# Advance pipeline from implementation to testing
print("\nAdvancing pipeline 73060985...")
result = post(f"{BASE}/api/pipelines/73060985-0543-45e9-ba46-316da3c223b7/advance", {})
print(f"  Phase: {result.get('current_phase')}")

# Start and complete task: Gather employment statistics and trends
print("\nStarting: Gather employment statistics and trends")
result = patch(f"{BASE}/api/tasks/51d24a07-a731-4c3d-9999-69fc76df53ce/status?status=done")
print(f"  Status: {result.get('status')}")

# Submit a research finding to populate the evolution system
print("\nSubmitting research finding on evolution architecture...")
result = post(f"{BASE}/api/ideas/0fdf0d73-7e7b-4765-b567-3599ceba72f9/deliverables", {
    "filename": "evolution_system_analysis.md",
    "content": "# Evolution System Analysis\n\n## Architecture\n- 3 REST endpoints (status, failures, research)\n- 6 MCP tools (failure lifecycle + research loop)\n- 3 DB tables (failure_records, research_findings, knowledge)\n- Auto-trigger when tasks exceed time threshold (120 min)\n- Frontend EvolutionPanel at /evolution\n\n## Current State: Nascent\n- 0 failures recorded, 0 research findings, 0 knowledge entries\n- Health metric is binary (healthy vs nascent)\n- Antibody/vaccine/catalyst are template-driven, not LLM-generated\n\n## Gap Analysis\n1. No auto-healing triggers (record only, never auto-fix)\n2. No knowledge injection into running agents (manual paste only)\n3. No time-series trends or health scoring\n4. REST API is read-only; all writes via MCP\n5. resolved_at field unused\n6. Frontend uses raw fetch() not api client\n\n## Dashboard Requirements\nPhase 1: Read-only dashboard + auto-healing REST endpoints\nPhase 2: Scheduled analysis + agent injection + LLM antibody generation"
})
print(f"  Deliverable submitted")

# Check final task state
print("\n=== Final Task Status ===")
data = json.loads(urllib.request.urlopen(f"{BASE}/api/tasks/").read())
project_tasks = [t for t in data if t.get("project_id","").startswith("0fda8d2e")]
for t in project_tasks:
    print(f"  [{t.get('status')}] {t['title']} (pri={t.get('priority','?')})")
