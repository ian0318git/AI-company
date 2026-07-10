"""Check task API schemas."""
import json, urllib.request

resp = urllib.request.urlopen('http://127.0.0.1:8765/openapi.json')
spec = json.loads(resp.read())

# Task status patch
sp = spec['paths']['/api/tasks/{task_id}/status']['patch']
print("=== PATCH status schema ===")
print(json.dumps(sp, indent=2))

# Task POST schema
post_sp = spec['paths']['/api/tasks/']['post']
print("\n=== POST task schema ===")
print(json.dumps(post_sp, indent=2))

# Idea start schema
start_sp = spec['paths'].get('/api/ideas/{idea_id}/start', {}).get('post', {})
print("\n=== POST idea/start schema ===")
print(json.dumps(start_sp, indent=2))
