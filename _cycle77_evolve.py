"""Inspect evolution tables and recent activity."""
import sqlite3

conn = sqlite3.connect("data/ai_embedded_company.db")

# Antibody candidates
cur = conn.execute("PRAGMA table_info(antibody_candidates)")
cols = [r[1] for r in cur.fetchall()]
print("=== ANTIBODY CANDIDATES ===")
cur = conn.execute("SELECT * FROM antibody_candidates ORDER BY id")
for r in cur.fetchall():
    print(f"  {r}")

# Event logs
cur = conn.execute("PRAGMA table_info(event_logs)")
cols = [r[1] for r in cur.fetchall()]
print(f"\n=== EVENT LOGS ({', '.join(cols)}) ===")
cur = conn.execute("SELECT * FROM event_logs ORDER BY id DESC LIMIT 15")
for r in cur.fetchall():
    print(f"  {r}")

# Research findings
cur = conn.execute("SELECT * FROM research_findings ORDER BY id")
print("\n=== RESEARCH FINDINGS ===")
for r in cur.fetchall():
    print(f"  {r}")

# Prompt templates
cur = conn.execute("SELECT id, name, system_prompt[:80] FROM prompt_templates ORDER BY id")
print("\n=== PROMPT TEMPLATES ===")
for r in cur.fetchall():
    print(f"  ID={r[0]} \"{r[1]}\" → {r[2]}...")

conn.close()
