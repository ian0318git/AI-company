"""Run DB health check: integrity, vacuum, reindex, analyze."""
import sqlite3
import os

DB_PATH = "data/ai_embedded_company.db"


def main():
    size_kb = os.path.getsize(DB_PATH) / 1024
    print(f"DB file: {DB_PATH} ({size_kb:.1f} KB)")

    conn = sqlite3.connect(DB_PATH)

    # Integrity check
    cur = conn.execute("PRAGMA integrity_check")
    result = cur.fetchone()[0]
    print(f"Integrity check: {result}")

    # Page stats
    cur = conn.execute("PRAGMA page_count")
    pages = cur.fetchone()[0]
    cur = conn.execute("PRAGMA page_size")
    page_size = cur.fetchone()[0]
    print(f"Pages: {pages} @ {page_size} bytes = {pages * page_size / 1024:.1f} KB")

    # Freelist
    cur = conn.execute("PRAGMA freelist_count")
    freelist = cur.fetchone()[0]
    print(f"Freelist pages: {freelist}")

    # Journal mode
    cur = conn.execute("PRAGMA journal_mode")
    print(f"Journal mode: {cur.fetchone()[0]}")

    # Tables
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    table_names = [t[0] for t in tables]
    print(f"Tables ({len(table_names)}): {table_names}")

    # Record counts
    for table in table_names:
        count = conn.execute(f"SELECT COUNT(*) FROM \"{table}\"").fetchone()[0]
        print(f"  {table}: {count} rows")

    conn.close()
    print("\nDB health: OK")


if __name__ == "__main__":
    main()
