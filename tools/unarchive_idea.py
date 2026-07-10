"""Unarchive an idea by setting its status back to 'pending'."""

import asyncio, sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

IDEA_ID = sys.argv[1] if len(sys.argv) > 1 else "522fdfee-df1e-4883-81d3-535594b968ae"

async def main():
    engine = create_async_engine("sqlite+aiosqlite:///data/ai_embedded_company.db")
    async with engine.connect() as conn:
        r = await conn.execute(
            text("SELECT id, title, status FROM ideas WHERE id=:id"), {"id": IDEA_ID}
        )
        row = r.fetchone()
        if row is None:
            print(f"Idea {IDEA_ID} not found")
            return 1
        print(f"Current: title={row[1][:50]}, status={row[2]}")

        await conn.execute(
            text("UPDATE ideas SET status='pending' WHERE id=:id"), {"id": IDEA_ID}
        )
        await conn.commit()

        r2 = await conn.execute(
            text("SELECT status FROM ideas WHERE id=:id"), {"id": IDEA_ID}
        )
        new_status = r2.scalar()
        print(f"New status: {new_status}")
        print("Unarchived successfully")
    await engine.dispose()
    return 0

sys.exit(asyncio.run(main()))
