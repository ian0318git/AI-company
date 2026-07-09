#!/usr/bin/env python3
"""Audit evolution-related tables for Cycle #231."""
import sqlite3
import json

conn = sqlite3.connect("data/ai_embedded_company.db")
cur = conn.cursor()

# Find evolution/failure/antibody tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
all_tables = [r[0] for r in cur.fetchall()]

evolution_tables = [t for t in all_tables if any(kw in t.lower() for kw in ["evolution", "failure", "antibody", "vaccine", "optimization"])]

print(f"All tables: {len(all_tables)}")
print(f"Evolution-related tables: {len(evolution_tables)}")
print()

for t in evolution_tables:
    cur.execute(f'SELECT COUNT(*) FROM "{t}"')
    cnt = cur.fetchone()[0]
    cur.execute(f'PRAGMA table_info("{t}")')
    cols = [r[1] for r in cur.fetchall()]
    print(f"=== {t} ({cnt} rows) ===")
    print(f"  Columns: {cols}")
    if cnt > 0:
        cur.execute(f'SELECT * FROM "{t}" LIMIT 3')
        for row in cur.fetchall():
            print(f"  {row}")
    print()

# Also check tasks for evolution-related ones
cur.execute("SELECT id, title, status FROM tasks WHERE title LIKE '%evolution%' OR title LIKE '%failure%' OR title LIKE '%antibody%'")
evo_tasks = cur.fetchall()
print(f"Evolution-related tasks: {len(evo_tasks)}")
for t in evo_tasks:
    print(f"  {t}")

conn.close()
print("Done.")
