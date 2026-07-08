import json, sys
d = json.load(sys.stdin)
schemas = d.get("components", {}).get("schemas", {})
# IdeaCreate schema
ic = schemas.get("IdeaCreate", {})
print("IdeaCreate schema:")
print(json.dumps(ic, indent=2)[:500])
# TaskStatusUpdate schema
tsu = schemas.get("TaskStatusUpdate", {})
print("\nTaskStatusUpdate schema:")
print(json.dumps(tsu, indent=2)[:500])
# Health schema
hs = schemas.get("HealthResponse", {})
print("\nHealthResponse schema:")
print(json.dumps(hs, indent=2)[:300])
