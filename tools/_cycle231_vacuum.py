#!/usr/bin/env python3
"""Vacuum and reindex the database."""
import sqlite3, os

db_path = "data/ai_embedded_company.db"
size_before = os.path.getsize(db_path)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("PRAGMA auto_vacuum=FULL")
cur.execute("VACUUM")
cur.execute("REINDEX")
conn.commit()

cur.execute("PRAGMA freelist_count")
fl = cur.fetchone()[0]
cur.execute("PRAGMA page_count")
pc = cur.fetchone()[0]
cur.execute("PRAGMA page_size")
ps = cur.fetchone()[0]

conn.close()

size_after = os.path.getsize(db_path)
saved = size_before - size_after

print(f"Before: {size_before/1024:.1f} KB")
print(f"After:  {size_after/1024:.1f} KB")
print(f"Saved:  {saved/1024:.1f} KB")
print(f"Pages: {pc}, Freelist: {fl}")
print("DB optimized successfully!")
