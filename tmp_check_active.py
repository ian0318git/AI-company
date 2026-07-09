#!/usr/bin/env python3
import json, subprocess, sys

r = subprocess.run(['curl', '-s', 'http://127.0.0.1:8765/api/ideas/'], capture_output=True, text=True)
try:
    ideas = json.loads(r.stdout)
except:
    print("Failed to parse ideas:", r.stdout[:200])
    sys.exit(1)

print("=== Non-done ideas ===")
for i in ideas:
    if i['status'] != 'done':
        print("  [%s] %s (id:%s)" % (i['status'], i['title'], i['id'][:12]))

print("\n=== All pipelines ===")
r2 = subprocess.run(['curl', '-s', 'http://127.0.0.1:8765/api/pipelines/'], capture_output=True, text=True)
pipes = json.loads(r2.stdout)
for p in sorted(pipes, key=lambda x: x['created_at']):
    if p['current_phase'] != 'done':
        print("  [%s] %s (id:%s)" % (p['current_phase'], p['pipeline_type'], p['id'][:12]))
