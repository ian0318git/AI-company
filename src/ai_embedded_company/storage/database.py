"""Async database connection and session management."""

from __future__ import annotations

import logging
import time
from typing import Any, AsyncIterator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from ai_embedded_company.config import get_settings

logger = logging.getLogger(__name__)

# ── Query profiling (Phase 2 of API Performance Profiling) ──────────────────
# Tracks per-statement execution time and logs queries exceeding the threshold.

SLOW_QUERY_THRESHOLD_MS = 100  # Log queries slower than this

_query_timings: dict[int, float] = {}  # connection_id -> start_time


def _before_cursor_execute(
    conn: Any,
    cursor: Any,
    statement: str,
    parameters: Any,
    context: Any | None,
    executemany: bool,
) -> None:
    """Record the start time before each statement executes."""
    _query_timings[id(conn)] = time.perf_counter()


def _after_cursor_execute(
    conn: Any,
    cursor: Any,
    statement: str,
    parameters: Any,
    context: Any | None,
    executemany: bool,
) -> None:
    """Log query duration if it exceeds the slow threshold."""
    start = _query_timings.pop(id(conn), None)
    if start is None:
        return
    elapsed_ms = (time.perf_counter() - start) * 1000
    if elapsed_ms >= SLOW_QUERY_THRESHOLD_MS:
        # Truncate long statements for readability
        stmt_short = statement.strip()[:120]
        logger.warning(
            "🐢 Slow query (%.0f ms): %s",
            elapsed_ms, stmt_short,
        )


# ── Engine & Sessions ───────────────────────────────────────────────────────


class Base(DeclarativeBase):
    pass


_engine = None
_sessionmaker = None
_wal_applied = False
_profiling_attached = False


def _get_engine():
    global _engine, _wal_applied, _profiling_attached
    if _engine is None:
        settings = get_settings()
        db_url = settings.database_url

        # Ensure data directory exists for SQLite
        if "sqlite" in db_url:
            db_path = settings.database_path
            db_path.parent.mkdir(parents=True, exist_ok=True)

        _engine = create_async_engine(
            db_url,
            echo=False,
            connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
        )

        # Enable SQLite WAL (Write-Ahead Logging) for concurrent read performance
        if "sqlite" in db_url and not _wal_applied:
            @event.listens_for(_engine.sync_engine, "connect")
            def _set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.close()
            _wal_applied = True
            logger.info("🔧 SQLite WAL mode enabled for concurrent read performance")

        # Attach query profiling listeners (run once per engine lifetime)
        if not _profiling_attached:
            event.listen(_engine.sync_engine, "before_cursor_execute", _before_cursor_execute)
            event.listen(_engine.sync_engine, "after_cursor_execute", _after_cursor_execute)
            _profiling_attached = True
            logger.info(
                "📊 Query profiling attached — slow query threshold: %d ms",
                SLOW_QUERY_THRESHOLD_MS,
            )

    return _engine


def _get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _sessionmaker


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return the global async session factory.

    Use this in cancellation-sensitive contexts (e.g. WebSocket handlers)
    to create sessions directly with ``async with get_sessionmaker() as s:``
    instead of using the ``get_session`` async generator, which can hit
    ``IllegalStateChangeError`` during generator cleanup on cancellation.
    """
    return _get_sessionmaker()


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield an async database session (FastAPI dependency).

    The ``async with`` context manager handles close automatically
    when the generator is cleaned up.
    """
    from sqlalchemy.exc import IllegalStateChangeError as _IllegalStateChangeError

    sessionmaker = _get_sessionmaker()
    async with sessionmaker() as session:
        try:
            yield session
        except _IllegalStateChangeError:
            # Raised when the calling coroutine is cancelled mid-query
            # (e.g. WebSocket disconnect) and the session state machine
            # is in a transition.  The session is being torn down, so
            # this is benign.
            logger.debug("Session generator cancelled — IllegalStateChangeError swallowed")


async def init_db():
    """Create all tables. Call on app startup."""
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Dispose the engine. Call on app shutdown."""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None
