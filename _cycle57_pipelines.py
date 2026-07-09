import json, sys
data = json.load(sys.stdin)
print(f"Total pipelines: {len(data)}")
for p in data:
    pid = p.get("id","?")[:8]
    phase = p.get("current_phase","?")
    ptype = p.get("pipeline_type","?")
    proj = p.get("project_id","?")[:8]
    print(f"  {pid} | phase={phase:12} | type={ptype:20} | project={proj}")
