#!/usr/bin/env python3
import json, subprocess, sys

r = subprocess.run(['curl', '-s', 'http://127.0.0.1:8765/api/ideas/'], capture_output=True)
raw = r.stdout
print("Ideas response length:", len(raw))
print("First 100 bytes:", raw[:100])
try:
    ideas = json.loads(raw.decode('utf-8'))
    active = [i for i in ideas if i['status'] != 'done']
    print("\nNon-done ideas:")
    for i in active:
        print("  [%s] %s" % (i['status'], i['title']))
except Exception as e:
    print("Parse error:", e)
