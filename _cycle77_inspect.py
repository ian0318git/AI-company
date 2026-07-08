"""Inspect database schema, all tables, and recent entries."""
import sqlite3

conn = sqlite3.connect("data/ai_embedded_company.db")

# List all tables
cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cur.fetchall()
print("=== ALL TABLES ===")
for (tname,) in tables:
    cur = conn.execute(f"SELECT COUNT(*) FROM \"{tname}\"")
    cnt = cur.fetchone()[0]
    print(f"  {tname}: {cnt} rows")

# Ideas schema & recent rows
cur = conn.execute("PRAGMA table_info(ideas)")
cols = [r[1] for r in cur.fetchall()]
print(f"\n=== IDEAS ({', '.join(cols)}) ===")
cur = conn.execute("SELECT * FROM ideas ORDER BY id DESC LIMIT 5")
for r in cur.fetchall():
    print(f"  {r}")

# Tasks schema & recent rows
cur = conn.execute("PRAGMA table_info(tasks)")
cols = [r[1] for r in cur.fetchall()]
print(f"\n=== TASKS ({', '.join(cols)}) ===")
cur = conn.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT 5")
for r in cur.fetchall():
    print(f"  {r}")

# Pipelines schema & recent rows
cur = conn.execute("PRAGMA table_info(pipelines)")
cols = [r[1] for r in cur.fetchall()]
print(f"\n=== PIPELINES ({', '.join(cols)}) ===")
cur = conn.execute("SELECT * FROM pipelines ORDER BY id DESC LIMIT 5")
for r in cur.fetchall():
    print(f"  {r}")

# Check event_log and evolution-related tables
for tbl in ["event_log", "antibodies", "vaccines", "failure_records", "knowledge"]:
    try:
        cur = conn.execute(f"SELECT * FROM \"{tbl}\" ORDER BY id DESC LIMIT 5")
        rows = cur.fetchall()
        cur2 = conn.execute(f"PRAGMA table_info(\"{tbl}\")")
        cols = [c[1] for c in cur2.fetchall()]
        print(f"\n=== {tbl.upper()} ({', '.join(cols)}) ===")
        for r in rows:
            print(f"  {r}")
    except Exception as e:
        print(f"\n=== {tbl}: SKIP ({e}) ===")

conn.close()
