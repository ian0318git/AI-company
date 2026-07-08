import json, sys
d = json.load(sys.stdin)
paths = d.get("paths", {})
# Task status update
ts = paths.get("/api/tasks/{task_id}/status", {})
print("PATCH /api/tasks/{task_id}/status:")
print(json.dumps(ts, indent=2)[:500])
# Ideas POST
ip = paths.get("/api/ideas/", {})
print("\nPOST /api/ideas/:")
post = ip.get("post", {})
print(json.dumps(post.get("requestBody", {}), indent=2)[:500])
print(f"Summary: {post.get('summary', 'N/A')}")
print(f"Tags: {post.get('tags', [])}")
# Health check
hp = paths.get("/health", {})
print("\nGET /health:")
print(json.dumps(hp, indent=2)[:300])
