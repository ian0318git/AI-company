#!/usr/bin/env python3
"""Cycle #142 health check: ideas, tasks, pipelines, cycles."""
import urllib.request, json, sqlite3, os
from datetime import datetime

def get_json(url):
    try:
        return json.loads(urllib.request.urlopen(url).read())
    except Exception as e:
        return f"ERROR: {e}"

# --- Ideas ---
ideas = get_json("http://127.0.0.1:8765/api/ideas/")
if isinstance(ideas, list):
    new = [i for i in ideas if i.get("status") in ("draft", "new", None, "")]
    print(f"Ideas: {len(ideas)} total, {len(new)} new/draft")
    for i in new:
        print(f"  NEW: {i['title']} (id={i['id']})")
else:
    print(f"Ideas: {ideas}")

# --- Tasks ---
tasks = get_json("http://127.0.0.1:8765/api/tasks/")
if isinstance(tasks, list):
    s = {}
    for t in tasks:
        st = t.get("status", "?")
        s[st] = s.get(st, 0) + 1
    print(f"\nTasks: {len(tasks)} total, statuses={json.dumps(s)}")
    active = [t for t in tasks if t.get("status") not in ("done", None, "")]
    print(f"Active tasks: {len(active)}")
    for t in active:
        print(f"  [{t.get('status')}] {t['title']} (pri={t.get('priority','?')})")
else:
    print(f"\nTasks: {tasks}")

# --- Pipelines ---
pipelines = get_json("http://127.0.0.1:8765/api/pipelines/")
if isinstance(pipelines, list):
    s = {}
    for p in pipelines:
        st = p.get("status", "?")
        s[st] = s.get(st, 0) + 1
        pid = p.get("id", "?")[:8]
        title = p.get("title", "?") or "?"
        status = p.get("status", "?")
        stage = p.get("stage", "?")
        print(f"  [{status}] {title} ({pid}...) stage={stage}")
    print(f"\nPipelines: {len(pipelines)} total, statuses={json.dumps(s)}")
else:
    print(f"\nPipelines: {pipelines}")

# --- DB: recent cycles ---
db_path = os.path.join(os.path.dirname(__file__), "data", "ai_embedded_company.db")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"\nDB tables: {tables}")
    if "cycle" in tables:
        cur.execute("SELECT cycle_number, status, summary, created_at FROM cycle ORDER BY cycle_number DESC LIMIT 5")
        print("Recent cycles:")
        for r in cur.fetchall():
            print(f"  #{r[0]} [{r[1]}] {r[2][:80] if r[2] else '?'} ({r[3]})")
    conn.close()
else:
    print(f"\nDB not found at {db_path}")

print(f"\n--- Cycle #142 Check Complete at {datetime.now().isoformat()} ---")
