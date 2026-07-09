"""Shared pagination helpers for list endpoints."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from ai_embedded_company.types import PaginatedResponse

T = TypeVar("T", bound=DeclarativeBase)


async def paginate_query(
    session: AsyncSession,
    stmt: Select,
    model_class: type[T],
    limit: int = 50,
    offset: int = 0,
    converter: Callable[[T], Any] | None = None,
) -> PaginatedResponse:
    """Execute a SELECT query with pagination and return a PaginatedResponse.

    Features:
      - Counts total matching rows using a subquery (avoids double-execution).
      - Applies limit/offset to the main query.
      - Computes next_offset and prev_offset for navigation.

    Args:
        session: SQLAlchemy async session.
        stmt: SELECT statement (before pagination is applied).
        model_class: The ORM model class (used for subquery typing).
        limit: Max items per page (default 50).
        offset: Number of items to skip (default 0).
        converter: Optional function to convert ORM models to Pydantic schema.
                   If None, the raw ORM model list is returned.

    Returns:
        PaginatedResponse with items (converted if converter is provided),
        total count, and navigation offsets.

    Usage:
        stmt = select(TaskModel).where(TaskModel.project_id == pid)
        return await paginate_query(
            session, stmt, TaskModel, limit=20, offset=0,
            converter=_model_to_task,
        )
    """
    # Count total matching rows
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    # Apply pagination
    paginated_stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(paginated_stmt)
    models = result.scalars().all()

    # Navigation offsets
    next_offset = offset + limit if offset + limit < total else None
    prev_offset = max(0, offset - limit) if offset > 0 else None

    # Convert models if converter is provided
    items = [converter(m) for m in models] if converter else list(models)

    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        next_offset=next_offset,
        prev_offset=prev_offset,
    )
