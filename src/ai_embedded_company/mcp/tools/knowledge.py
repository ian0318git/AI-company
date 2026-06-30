"""MCP tools for knowledge base management."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select

from ai_embedded_company.storage.database import _get_sessionmaker
from ai_embedded_company.storage.models import KnowledgeModel


def register_tools(mcp):
    """Register knowledge tools with the FastMCP instance."""

    @mcp.tool()
    async def knowledge_add(
        title: str,
        content: str,
        category: str = "tip",
        tags: str = "",
        board_family: str = "",
    ) -> dict:
        """Add an entry to the team knowledge base.

        Capture hard-won knowledge: bug fixes, pinout discoveries,
        code patterns, toolchain tricks.

        Args:
            title: Knowledge title (e.g., "BME280 I2C address is 0x76 not 0x77")
            content: Full content — code snippets, wiring notes, error messages
            category: Type: pinout, datasheet, code-pattern, bug-fix, tip
            tags: Comma-separated tags
            board_family: Target hardware family (esp32, stm32, etc.)
        """
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

        sessionmaker = _get_sessionmaker()
        async with sessionmaker() as session:
            entry = KnowledgeModel(
                title=title,
                content=content,
                category=category,
                tags=json.dumps(tag_list),
                board_family=board_family if board_family else None,
            )
            session.add(entry)
            await session.commit()
            await session.refresh(entry)

            return {
                "id": entry.id,
                "title": title,
                "category": category,
                "tags": tag_list,
                "message": "Knowledge entry added. Use knowledge_search to find it later.",
            }

    @mcp.tool()
    async def knowledge_search(
        query: str = "",
        category: str = "",
        board_family: str = "",
        limit: int = 15,
    ) -> dict:
        """Search the team knowledge base.

        Args:
            query: Search keywords (searches title + content)
            category: Filter by category: pinout, datasheet, code-pattern, bug-fix, tip
            board_family: Filter by hardware: esp32, esp32-s3, stm32, rp2040
            limit: Max results
        """
        sessionmaker = _get_sessionmaker()

        async with sessionmaker() as session:
            stmt = select(KnowledgeModel)

            if category:
                stmt = stmt.where(KnowledgeModel.category == category)
            if board_family:
                stmt = stmt.where(KnowledgeModel.board_family == board_family)

            stmt = stmt.order_by(KnowledgeModel.created_at.desc())
            result = await session.execute(stmt)
            all_entries = result.scalars().all()

            # Filter by query if provided
            entries = []
            for entry in all_entries:
                if not query or (query.lower() in entry.title.lower() or query.lower() in (entry.content or "").lower()):
                    try:
                        tags = json.loads(entry.tags) if entry.tags else []
                    except (json.JSONDecodeError, TypeError):
                        tags = []
                    entries.append({
                        "id": entry.id,
                        "title": entry.title,
                        "category": entry.category,
                        "tags": tags,
                        "board_family": entry.board_family,
                        "snippet": (entry.content or "")[:300],
                        "created_at": entry.created_at.isoformat() if entry.created_at else None,
                    })

            entries = entries[:limit]

            return {
                "query": query or "(all)",
                "results": entries,
                "count": len(entries),
            }

    @mcp.tool()
    async def knowledge_load_board(board_model: str) -> dict:
        """Load built-in hardware knowledge for a specific development board.

        Args:
            board_model: Board model (e.g., "m5stack-core-s3")
        """
        kb_dir = Path(__file__).parent.parent.parent / "knowledge"
        kb_file = kb_dir / f"{board_model}.json"

        if kb_file.exists():
            try:
                return json.loads(kb_file.read_text())
            except (json.JSONDecodeError, IOError) as e:
                return {"error": f"Failed to load knowledge: {e}"}

        return {
            "error": f"No built-in knowledge for '{board_model}'.",
            "available": [f.stem for f in kb_dir.glob("*.json")],
        }
