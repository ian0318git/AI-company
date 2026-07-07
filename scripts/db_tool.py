#!/usr/bin/env python3
"""Database backup & protection tool.

Usage:
    uv run python scripts/db_tool.py backup     # Create a timestamped backup
    uv run python scripts/db_tool.py list       # List all backups
    uv run python scripts/db_tool.py restore    # Interactive restore from backup
    uv run python scripts/db_tool.py restore <name>  # Restore specific backup
    uv run python scripts/db_tool.py status     # Show DB status
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BACKUP_DIR = Path("data/db_backups")
DB_PATH = Path("data/ai_embedded_company.db")


def _ensure_backup_dir():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def _db_exists() -> bool:
    return DB_PATH.exists() and DB_PATH.stat().st_size > 0


def _db_size() -> str:
    if not DB_PATH.exists():
        return "N/A"
    size = DB_PATH.stat().st_size
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def _count_tables(db_path: Path) -> dict:
    """Count records in key tables without needing the app."""
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        tables = ["projects", "ideas", "tasks", "pipelines", "teams", "failure_records"]
        counts = {}
        for t in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                counts[t] = cur.fetchone()[0]
            except Exception:
                counts[t] = "?"
        conn.close()
        return counts
    except Exception as e:
        return {"error": str(e)}


def cmd_backup():
    """Create a timestamped backup of the current database."""
    _ensure_backup_dir()

    if not _db_exists():
        print("❌ No database found to backup.")
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"ai_embedded_company_{timestamp}.db"

    shutil.copy2(DB_PATH, backup_path)

    counts = _count_tables(DB_PATH)
    size = _db_size()

    print(f"✅ Backup created: {backup_path.name}")
    print(f"   Size: {size}")
    print(f"   Tables: {json.dumps(counts)}")
    return True


def cmd_list():
    """List all available backups."""
    _ensure_backup_dir()
    backups = sorted(BACKUP_DIR.glob("*.db"), reverse=True)

    if not backups:
        print("📂 No backups found.")
        return

    print(f"📂 Backups in {BACKUP_DIR}/")
    print(f"{'#':>3}  {'Name':<55} {'Size':<10} {'Tables'}")
    print("-" * 90)
    for i, b in enumerate(backups, 1):
        size = b.stat().st_size
        size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024*1024):.1f} MB"
        counts = _count_tables(b)
        tables_str = " ".join(f"{k}={v}" for k, v in counts.items() if v != "?")
        print(f"{i:>3}  {b.name:<55} {size_str:<10} {tables_str}")


def cmd_restore(name: str | None = None):
    """Restore a backup."""
    _ensure_backup_dir()
    backups = sorted(BACKUP_DIR.glob("*.db"), reverse=True)

    if not backups:
        print("❌ No backups available to restore.")
        return

    if name:
        matches = [b for b in backups if name in b.name]
        if not matches:
            print(f"❌ No backup matching '{name}' found.")
            cmd_list()
            return
        backup_path = matches[0]
    else:
        cmd_list()
        print()
        try:
            idx = int(input("Enter backup # to restore: ").strip()) - 1
            backup_path = backups[idx]
        except (ValueError, IndexError):
            print("❌ Invalid selection.")
            return

    # Preview what will be restored
    counts = _count_tables(backup_path)
    print(f"\n📋 Backup: {backup_path.name}")
    print(f"   Tables: {json.dumps(counts)}")

    current_counts = _count_tables(DB_PATH) if _db_exists() else {}
    if current_counts:
        print(f"   Current DB: {json.dumps(current_counts)}")

    confirm = input("\n⚠️  Restore will OVERWRITE current database. Continue? [y/N] ").strip().lower()
    if confirm != "y":
        print("❌ Restore cancelled.")
        return

    # Auto-backup current DB before overwriting
    if _db_exists():
        auto_backup = BACKUP_DIR / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(DB_PATH, auto_backup)
        print(f"💾 Current DB backed up: {auto_backup.name}")

    shutil.copy2(backup_path, DB_PATH)
    print(f"✅ Restored: {backup_path.name}")
    print(f"   Size: {_db_size()}")


def cmd_status():
    """Show current database status."""
    if _db_exists():
        counts = _count_tables(DB_PATH)
        print(f"📊 Database: {DB_PATH}")
        print(f"   Size: {_db_size()}")
        print(f"   Last modified: {datetime.fromtimestamp(DB_PATH.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Tables: {json.dumps(counts)}")

        # Show latest backup
        _ensure_backup_dir()
        backups = sorted(BACKUP_DIR.glob("*.db"), reverse=True)
        if backups:
            latest = backups[0]
            age = datetime.now() - datetime.fromtimestamp(latest.stat().st_mtime)
            age_str = f"{age.days}d {age.seconds // 3600}h" if age.days else f"{age.seconds // 3600}h {(age.seconds % 3600) // 60}m"
            print(f"\n💾 Latest backup: {latest.name} ({age_str} ago)")
    else:
        print("❌ No database found.")
        print(f"   Expected at: {DB_PATH.resolve()}")


if __name__ == "__main__":
    if not BACKUP_DIR.parent.exists():
        print(f"❌ Data directory not found: {BACKUP_DIR.parent.resolve()}")
        sys.exit(1)

    args = sys.argv[1:]
    if not args:
        print(__doc__.strip())
        sys.exit(0)

    command = args[0]
    if command == "backup":
        cmd_backup()
    elif command == "list":
        cmd_list()
    elif command == "restore":
        cmd_restore(args[1] if len(args) > 1 else None)
    elif command == "status":
        cmd_status()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
