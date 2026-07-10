"""Run DB health checks: integrity, optimize, index analysis."""

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    engine = create_async_engine("sqlite+aiosqlite:///data/ai_embedded_company.db")
    async with engine.connect() as conn:
        r = await conn.execute(text("PRAGMA integrity_check"))
        integrity = r.scalar()
        print(f"Integrity check: {integrity}")

        await conn.execute(text("PRAGMA optimize"))
        print("PRAGMA optimize done")

        r2 = await conn.execute(text("PRAGMA page_count"))
        pages = r2.scalar()
        r3 = await conn.execute(text("PRAGMA page_size"))
        page_size = r3.scalar()
        print(f"Database: {pages} pages x {page_size}B = {pages * page_size / 1024:.1f} KB")

        r4 = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        )
        indexes = [row[0] for row in r4.fetchall()]
        print(f"Custom indexes ({len(indexes)}): {indexes}")

        r5 = await conn.execute(
            text("SELECT COUNT(*) FROM failure_records")
        )
        failures = r5.scalar()
        print(f"Evolution failure records: {failures}")

        r6 = await conn.execute(
            text("SELECT id, title, status FROM ideas WHERE status != 'done' AND status != 'archived'")
        )
        for row in r6.fetchall():
            print(f"Active idea: {row[1][:50]} [{row[2]}]")

    await engine.dispose()

asyncio.run(main())
