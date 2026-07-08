"""Cycle 77 — scan ideas, tasks, pipelines from database."""
import sqlite3
import os

dbfile = "data/ai_embedded_company.db"
if not os.path.exists(dbfile):
    print(f"DB not found at {dbfile}")
else:
    conn = sqlite3.connect(dbfile)

    # Ideas
    cur = conn.execute("SELECT status, COUNT(*) FROM ideas GROUP BY status ORDER BY COUNT(*) DESC")
    print("=== IDEAS BY STATUS ===")
    for r in cur.fetchall():
        print(f"  {r[0]}: {r[1]}")

    cur = conn.execute("SELECT id, title, status FROM ideas WHERE status != 'done' ORDER BY id")
    print("\n=== NON-DONE IDEAS ===")
    for r in cur.fetchall():
        print(f"  ID={r[0]} \"{r[1]}\" status={r[2]}")

    # Tasks
    cur = conn.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status ORDER BY COUNT(*) DESC")
    print("\n=== TASKS BY STATUS ===")
    for r in cur.fetchall():
        print(f"  {r[0]}: {r[1]}")

    cur = conn.execute("SELECT id, title, status, priority FROM tasks WHERE status IN ('todo', 'in_progress') ORDER BY priority, id")
    print("\n=== TODO/IN_PROGRESS TASKS ===")
    for r in cur.fetchall():
        print(f"  ID={r[0]} [{r[3]}] {r[1]} — status={r[2]}")

    # Pipelines
    cur = conn.execute("SELECT current_phase, COUNT(*) FROM pipelines GROUP BY current_phase ORDER BY COUNT(*) DESC")
    print("\n=== PIPELINES BY PHASE ===")
    for r in cur.fetchall():
        print(f"  phase={r[0]}: {r[1]}")

    cur = conn.execute("SELECT id, name, current_phase FROM pipelines WHERE current_phase != 'done' ORDER BY id")
    print("\n=== NON-DONE PIPELINES ===")
    for r in cur.fetchall():
        print(f"  ID={r[0]} \"{r[1]}\" phase={r[2]}")

    conn.close()
