"""Conclude stalled A/B experiments and generate baseline insights for Cycle #78."""
import json, sys, urllib.request

BASE = "http://127.0.0.1:8765"

# 1. Get all experiments
req = urllib.request.Request(f"{BASE}/api/prompts/experiments")
with urllib.request.urlopen(req) as resp:
    experiments = json.loads(resp.read())

print("=== A/B Experiments ===")
stalled = []
for exp in experiments:
    total = exp["control_total"] + exp["variant_total"]
    print(f"  {exp['experiment_name']:40s} | status={exp['status']:10s} | samples={total}")
    if exp["status"] == "running" and total == 0:
        stalled.append(exp["id"])

# 2. Conclude stalled experiments as inconclusive
print(f"\nConcluding {len(stalled)} stalled experiments (0 samples, no tasks to sample)...")
for eid in stalled:
    data = json.dumps({"status": "inconclusive", "reason": "No tasks created during experiment window — 0 samples collected across 206 completed tasks."}).encode()
    req = urllib.request.Request(f"{BASE}/api/prompts/experiments/{eid}/conclude", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            print(f"  Concluded: {result}")
    except Exception as e:
        print(f"  Error concluding {eid}: {e}")

# 3. Check if there's anything in insights
req = urllib.request.Request(f"{BASE}/api/prompts/insights")
with urllib.request.urlopen(req) as resp:
    insights = json.loads(resp.read())
print(f"\nExisting insights: {len(insights)}")

# 4. Try to generate insights from task data
insight_data = json.dumps({
    "source": "cycle_78_health_check",
    "total_tasks": 206,
    "done_tasks": 206,
    "avg_completion_minutes": 12.7,
    "total_tokens": 85350,
}).encode()
req = urllib.request.Request(f"{BASE}/api/prompts/insights/generate", data=insight_data, method="POST")
req.add_header("Content-Type", "application/json")
try:
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        print(f"Insights generated: {json.dumps(result, indent=2)[:300]}")
except Exception as e:
    print(f"Error generating insights: {e}")

# 5. Run evolution classification to ensure failure records are fresh
try:
    req = urllib.request.Request(f"{BASE}/api/evolution/classify", data=b"{}", method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        print(f"\nEvolution classify: {json.dumps(result, indent=2)[:300]}")
except Exception as e:
    print(f"Classification: {e}")

print("\n=== Cycle #78 clean-up complete ===")
