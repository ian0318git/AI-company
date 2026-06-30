"""MCP tools for project memory and search."""

from __future__ import annotations

import json

from sqlalchemy import select

from ai_embedded_company.storage.database import _get_sessionmaker
from ai_embedded_company.storage.models import EventLogModel, KnowledgeModel, TaskModel


def register_tools(mcp):
    """Register memory/search tools with the FastMCP instance."""

    @mcp.tool()
    async def memory_search(
        query: str,
        project_id: str = "",
        limit: int = 10,
    ) -> dict:
        """Search project memory for relevant context.

        Searches across tasks, knowledge entries, and event logs for anything
        matching your query. Useful for recalling past decisions, bug fixes,
        and implementation details.

        Args:
            query: Search query (keywords)
            project_id: Limit search to a specific project (optional)
            limit: Max results to return (default: 10)
        """
        sessionmaker = _get_sessionmaker()
        results = []

        async with sessionmaker() as session:
            # Search tasks
            task_stmt = select(TaskModel)
            if project_id:
                task_stmt = task_stmt.where(TaskModel.project_id == project_id)
            task_result = await session.execute(task_stmt)
            for task in task_result.scalars().all():
                if _matches(task.title, query) or _matches(task.description, query):
                    results.append({
                        "type": "task",
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "snippet": (task.description or "")[:200],
                    })

            # Search knowledge
            kb_stmt = select(KnowledgeModel)
            kb_result = await session.execute(kb_stmt)
            for kb in kb_result.scalars().all():
                if _matches(kb.title, query) or _matches(kb.content, query):
                    results.append({
                        "type": "knowledge",
                        "id": kb.id,
                        "title": kb.title,
                        "category": kb.category,
                        "snippet": (kb.content or "")[:300],
                    })

            # Search event logs
            event_stmt = select(EventLogModel).order_by(EventLogModel.created_at.desc()).limit(50)
            event_result = await session.execute(event_stmt)
            for evt in event_result.scalars().all():
                payload = evt.payload or "{}"
                if _matches(payload, query):
                    try:
                        payload_data = json.loads(payload)
                        if isinstance(payload_data, dict):
                            msg = payload_data.get("message", payload_data.get("summary", ""))
                            if msg:
                                results.append({
                                    "type": "event",
                                    "event_type": evt.event_type,
                                    "timestamp": evt.created_at.isoformat() if evt.created_at else None,
                                    "snippet": str(msg)[:300],
                                })
                    except (json.JSONDecodeError, TypeError):
                        pass

        results = results[:limit]

        return {
            "query": query,
            "results": results,
            "count": len(results),
            "message": f"Found {len(results)} results for '{query}'." if results else f"No results for '{query}'.",
        }

    @mcp.tool()
    async def team_knowledge() -> dict:
        """Get team-wide knowledge and project statistics.

        Returns an overview of all projects, task counts, and recent activity.
        """
        sessionmaker = _get_sessionmaker()

        async with sessionmaker() as session:
            # Project count
            from ai_embedded_company.storage.models import ProjectModel

            proj_result = await session.execute(select(ProjectModel))
            projects = proj_result.scalars().all()

            task_result = await session.execute(select(TaskModel))
            tasks = task_result.scalars().all()

            kb_result = await session.execute(select(KnowledgeModel))
            kb_entries = kb_result.scalars().all()

            task_by_status = {}
            for t in tasks:
                task_by_status[t.status] = task_by_status.get(t.status, 0) + 1

            return {
                "projects": len(projects),
                "active_projects": len([p for p in projects if p.status == "active"]),
                "total_tasks": len(tasks),
                "tasks_by_status": task_by_status,
                "knowledge_entries": len(kb_entries),
                "recent_activity": "Use memory_search for detailed activity.",
            }


def _matches(text: str, query: str) -> bool:
    """Simple case-insensitive substring match."""
    if not text or not query:
        return False
    return query.lower() in text.lower()
