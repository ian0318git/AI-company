"""Check task status for cycle 26."""
import json, urllib.request
from collections import Counter

data = json.loads(urllib.request.urlopen("http://127.0.0.1:8765/api/tasks/").read())
for t in data:
    s = t.get("status", "?")
    if s not in ("done", "cancelled"):
        print(f"  [{s}] {t['title']} (pri={t.get('priority','?')})")
c = Counter(t.get("status","?") for t in data)
print(f"\nSummary: {dict(c)}")
print(f"Total: {len(data)}")
