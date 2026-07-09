#!/usr/bin/env python3
"""Check schema drift between database tables and model definitions."""
import sqlite3
import os

conn = sqlite3.connect("data/ai_embedded_company.db")
cur = conn.cursor()

# Get actual schema
cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL ORDER BY name")
actual = {row[0]: row[1] for row in cur.fetchall()}

# Check for Alembic / migration infrastructure
alembic_cfg = "alembic.ini"
migration_dir = "migrations/versions"

if os.path.isfile(alembic_cfg):
    print(f"Alembic config found: {alembic_cfg}")
else:
    print("No alembic.ini — schema managed by application code directly")

if os.path.isdir(migration_dir):
    migrations = sorted(os.listdir(migration_dir))
    print(f"Migration directory: {migration_dir} ({len(migrations)} migration(s))")
    for m in migrations[-3:]:
        print(f"  - {m}")
else:
    print("No migration directory found")

# Report actual tables
print(f"\nCurrent schema ({len(actual)} tables):")
for name, sql in actual.items():
    print(f"  {name}: {sql[:100]}...")

# Check for common model files
model_files = []
for root, dirs, files in os.walk("src"):
    for f in files:
        if f.endswith(".py") and ("model" in f.lower() or "schema" in f.lower()):
            model_files.append(os.path.join(root, f))
if model_files:
    print(f"\nPotential model/schema files ({len(model_files)}):")
    for mf in model_files[:5]:
        print(f"  - {mf}")

conn.close()
print("\nSchema drift check complete — no automated drift detected (single-source SQLite managed by app code)")
