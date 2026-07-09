#!/usr/bin/env python3
"""Database health check script for Cycle #231."""
import sqlite3
import os
import json
from datetime import datetime, timezone

db_path = "data/ai_embedded_company.db"
results: dict[str, object] = {
    "check_time": datetime.now(timezone.utc).isoformat(),
    "db_path": db_path,
}

# File info
size_bytes = os.path.getsize(db_path)
results["file_size_bytes"] = size_bytes
results["file_size_mb"] = round(size_bytes / 1024 / 1024, 2)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 1. Integrity check
cur.execute("PRAGMA integrity_check")
integrity = cur.fetchone()[0]
results["integrity_check"] = integrity
if integrity != "ok":
    results["integrity_issue"] = True
    print(f"WARNING: Integrity check failed: {integrity}")
else:
    print("OK: Integrity check passed")

# 2. Page stats
cur.execute("PRAGMA page_count")
pages = cur.fetchone()[0]
cur.execute("PRAGMA page_size")
page_size = cur.fetchone()[0]
cur.execute("PRAGMA freelist_count")
freelist = cur.fetchone()[0]

results["page_count"] = pages
results["page_size"] = page_size
results["freelist_pages"] = freelist
results["wasted_kb"] = round(freelist * page_size / 1024, 1)
results["total_db_kb"] = round(pages * page_size / 1024, 1)

print(f"Pages: {pages} x {page_size}B = {results['total_db_kb']:.1f} KB")
print(f"Freelist (wasted): {freelist} pages = {results['wasted_kb']:.1f} KB")

# 3. Schema
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
table_rows: dict[str, int] = {}
for (tname,) in cur.fetchall():
    cur.execute(f'SELECT COUNT(*) FROM "{tname}"')
    table_rows[tname] = cur.fetchone()[0]
results["tables"] = table_rows
print(f"Tables: {len(table_rows)} — {sum(table_rows.values())} total rows")

# 4. Index analysis
cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
index_count = len(cur.fetchall())
results["index_count"] = index_count

# 5. Auto-vacuum
cur.execute("PRAGMA auto_vacuum")
av_map = {0: "none", 1: "full", 2: "incremental"}
results["auto_vacuum"] = av_map.get(cur.fetchone()[0], "unknown")

# 6. Schema comparison with backup
cur.execute("SELECT sql FROM sqlite_master WHERE type='table' ORDER BY name")
schema_sqls = [r[0] for r in cur.fetchall()]
results["schema_checksum"] = hash("\n".join(schema_sqls or []))
print(f"Schema hash: {results['schema_checksum']}")
print(f"Indices: {index_count}")
print(f"Auto-vacuum: {results['auto_vacuum']}")

conn.close()

# Write results
out_path = "tools/_cycle231_db_health_results.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nResults written to {out_path}")

# Summary for cycle report
healthy = integrity == "ok"
fragmented = results["wasted_kb"] > 10
if not healthy:
    print("NEEDS_ACTION: Integrity check failed!")
if fragmented:
    print(f"SUGGESTION: VACUUM recommended ({results['wasted_kb']:.1f} KB wasted)")
else:
    print("OK: Database is healthy and not fragmented")
